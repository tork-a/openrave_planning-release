#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2010 Rosen Diankov (rosen.diankov@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import with_statement # for python 2.5
__author__ = 'Rosen Diankov'
__copyright__ = 'Copyright (C) 2010 Rosen Diankov (rosen.diankov@gmail.com)'
__license__ = 'Apache License, Version 2.0'
import roslib; roslib.load_manifest('orrosplanning')
import rospy

roslib.load_manifest('object_manipulation_msgs')
from optparse import OptionParser
from openravepy import *
from openravepy.misc import OpenRAVEGlobalArguments
from numpy import *
import numpy,time,threading
from itertools import izip
import tf
import os

import sensor_msgs.msg
import trajectory_msgs.msg
import geometry_msgs.msg
import object_manipulation_msgs.srv
import object_manipulation_msgs.msg
import orrosplanning.srv

class FastGrasping:
    """Computes a valid grasp for a given object as fast as possible without relying on a pre-computed grasp set
    """
    class GraspingException(Exception):
        def __init__(self,args):
            self.args=args

    def __init__(self,robot,target,ignoreik=False,returngrasps=1):
        self.ignoreik=ignoreik
        self.returngrasps = returngrasps
        self.robot = robot
        self.ikmodel = databases.inversekinematics.InverseKinematicsModel(robot=robot,iktype=IkParameterization.Type.Transform6D)
        if not self.ikmodel.load():
            self.ikmodel.autogenerate()
        self.gmodel = databases.grasping.GraspingModel(robot,target)
        self.gmodel.init(friction=0.4,avoidlinks=[])
        self.jointvalues = []
        self.grasps = []

    def checkgraspfn(self, contacts,finalconfig,grasp,info):
        # check if grasp can be reached by robot
        Tglobalgrasp = self.gmodel.getGlobalGraspTransform(grasp,collisionfree=True)
        # have to set the preshape since the current robot is at the final grasp!
        self.gmodel.setPreshape(grasp)
        jointvalues = array(finalconfig[0])
        if self.ignoreik:
            if self.gmodel.manip.CheckEndEffectorCollision(Tglobalgrasp):
               return False

        else:
            sol = self.gmodel.manip.FindIKSolution(Tglobalgrasp,True)
            if sol is None:
                return False

            jointvalues[self.gmodel.manip.GetArmIndices()] = sol

        self.jointvalues.append(jointvalues)
        self.grasps.append(grasp)
        if len(self.jointvalues) < self.returngrasps:
            return True

        raise self.GraspingException((self.grasps,self.jointvalues))

    def computeGrasp(self,graspparameters):
        if len(graspparameters.approachrays) == 0:
            approachrays = self.gmodel.computeBoxApproachRays(delta=0.02,normalanglerange=0.5) # rays to approach object
        else:
            approachrays = reshape(graspparameters.approachrays,[len(graspparameters.approachrays)/6,6])

        Ttarget = self.gmodel.target.GetTransform()
        N = len(approachrays)
        gapproachrays = c_[dot(approachrays[:,0:3],transpose(Ttarget[0:3,0:3]))+tile(Ttarget[0:3,3],(N,1)),dot(approachrays[:,3:6],transpose(Ttarget[0:3,0:3]))]
        self.approachgraphs = [env.plot3(points=gapproachrays[:,0:3],pointsize=5,colors=array((1,0,0))),
                               env.drawlinelist(points=reshape(c_[gapproachrays[:,0:3],gapproachrays[:,0:3]+0.005*gapproachrays[:,3:6]],(2*N,3)),linewidth=4,colors=array((1,0,0,1)))]

        if len(graspparameters.standoffs) == 0:
            standoffs = [0]
        else:
            standoffs = graspparameters.standoffs
        if len(graspparameters.rolls) == 0:
            rolls = arange(0,2*pi,0.5*pi)
        else:
            rolls = graspparameters.rolls
        if len(graspparameters.preshapes) == 0:
            # initial preshape for robot is the released fingers
            with self.gmodel.target:
                self.gmodel.target.Enable(False)
                taskmanip = interfaces.TaskManipulation(self.robot)
                final,traj = taskmanip.ReleaseFingers(execute=False,outputfinal=True)
                preshapes = array([final])
        else:
            dim = len(self.gmodel.manip.GetGripperIndices())
            preshapes = reshape(graspparameters.preshapes,[len(graspparameters.preshapes)/dim,dim])
        try:
            self.gmodel.disableallbodies=False
            self.gmodel.generate(preshapes=preshapes,standoffs=standoffs,rolls=rolls,approachrays=approachrays,checkgraspfn=self.checkgraspfn,graspingnoise=0)
            return self.grasps,self.jointvalues
        except self.GraspingException, e:
            return e.args

if __name__ == "__main__":
    parser = OptionParser(description='openrave planning example')
    OpenRAVEGlobalArguments.addOptions(parser)
    parser.add_option('--scene',action="store",type='string',dest='scene',default='robots/pr2-beta-static.zae',
                      help='scene to load (default=%default)')
    parser.add_option('--collision_map',action="store",type='string',dest='collision_map',default='/collision_map/collision_map',
                      help='The collision map topic (maping_msgs/CollisionMap), by (default=%default)')
    parser.add_option('--ipython', '-i',action="store_true",dest='ipython',default=False,
                      help='if true will drop into the ipython interpreter rather than spin')
    parser.add_option('--mapframe',action="store",type='string',dest='mapframe',default=None,
                      help='The frame of the map used to position the robot. If --mapframe="" is specified, then nothing will be transformed with tf')
    parser.add_option('--returngrasps',action="store",type='int',dest='returngrasps',default=1,
                      help='return all the grasps')
    parser.add_option('--ignoreik',action="store_true",dest='ignoreik',default=False,
                      help='ignores the ik computations')
    (options, args) = parser.parse_args()
    env = OpenRAVEGlobalArguments.parseAndCreate(options,defaultviewer=False)
    RaveLoadPlugin(os.path.join(roslib.packages.get_pkg_dir('orrosplanning'),'lib','orrosplanning'))
    RaveLoadPlugin(os.path.join(roslib.packages.get_pkg_dir('openraveros'),'lib','openraveros'))
    namespace = 'openrave'
    env.AddModule(RaveCreateModule(env,'rosserver'),namespace)
    print 'initializing, please wait for ready signal...'

    graspparameters = orrosplanning.srv.SetGraspParametersRequest()
    envlock = threading.Lock()
    try:
        rospy.init_node('graspplanning_openrave',disable_signals=False)
        with env:
            env.Load(options.scene)
            robot = env.GetRobots()[0]

            # set robot weights/resolutions (without this planning will be slow)
#             lmodel = databases.linkstatistics.LinkStatisticsModel(robot)
#             if not lmodel.load():
#                 lmodel.autogenerate()
#             lmodel.setRobotWeights()
#             lmodel.setRobotResolutions()

            # create ground right under the robot
            ab=robot.ComputeAABB()
            ground=RaveCreateKinBody(env,'')
            ground.SetName('map')
            ground.InitFromBoxes(array([r_[ab.pos()-array([0,0,ab.extents()[2]+0.002]),2.0,2.0,0.001]]),True)
            env.AddKinBody(ground,False)
            if options.mapframe is None:
                options.mapframe = robot.GetLinks()[0].GetName()
                print 'setting map frame to %s'%options.mapframe
            if len(options.collision_map) > 0:
                collisionmap = RaveCreateSensorSystem(env,'CollisionMap bodyoffset %s topic %s'%(robot.GetName(),options.collision_map))
            basemanip = interfaces.BaseManipulation(robot)
            grasper = interfaces.Grasper(robot)

        listener = tf.TransformListener()
        values = robot.GetDOFValues()
        def UpdateRobotJoints(msg):
            with envlock:
                with env:
                    for name,pos in izip(msg.name,msg.position):
                        j = robot.GetJoint(name)
                        if j is not None:
                            values[j.GetDOFIndex()] = pos
                    robot.SetDOFValues(values)

        def trimeshFromPointCloud(pointcloud):
            points = zeros((len(pointcloud.points),3),double)
            for i,p in enumerate(pointcloud.points):
                points[i,0] = p.x
                points[i,1] = p.y
                points[i,2] = p.z
            cindices = [c.values for c in pointcloud.channels if c.name == 'indices']
            if len(cindices) > 0:
                vertices = points
                indices = reshape(array(cindices[0],int),(len(cindices[0])/3,3))
            else:
                # compute the convex hull triangle mesh
                meanpoint = mean(points,1)
                planes,faces,triangles = grasper.ConvexHull(points,returntriangles=True)
                usedindices = zeros(len(points),int)
                usedindices[triangles.flatten()] = 1
                pointindices = flatnonzero(usedindices)
                pointindicesinv = zeros(len(usedindices))
                pointindicesinv[pointindices] = range(len(pointindices))
                vertices = points[pointindices]
                indices = reshape(pointindicesinv[triangles.flatten()],triangles.shape)
            return TriMesh(vertices=vertices,indices=indices)
        def CreateTarget(graspableobject):
            target = RaveCreateKinBody(env,'')
            Ttarget = eye(4)
            if 1:#graspableobject.type == object_manipulation_msgs.msg.GraspableObject.POINT_CLUSTER:
                target.InitFromTrimesh(trimeshFromPointCloud(graspableobject.cluster),True)
                if len(options.mapframe) > 0:
                    (trans,rot) = listener.lookupTransform(options.mapframe, graspableobject.cluster.header.frame_id, rospy.Time(0))
                    Ttarget = matrixFromQuat([rot[3],rot[0],rot[1],rot[2]])
                    Ttarget[0:3,3] = trans
                else:
                    Ttarget = eye(4)
            else:
                raise ValueError('do not support graspable objects of type %s'%str(graspableobject.type))

            target.SetName('graspableobject')
            env.AddKinBody(target,True)
            target.SetTransform(Ttarget)
            return target

        def GraspPlanning(req):
            global graspparameters
            with envlock:
                with env:
                    # update the robot
                    if len(options.mapframe) > 0:
                        (robot_trans,robot_rot) = listener.lookupTransform(options.mapframe, robot.GetLinks()[0].GetName(), rospy.Time(0))
                        Trobot = matrixFromQuat([robot_rot[3],robot_rot[0],robot_rot[1],robot_rot[2]])
                        Trobot[0:3,3] = robot_trans
                        robot.SetTransform(Trobot)
                    # set the manipulator
                    if len(req.arm_name) > 0:
                        manip = robot.GetManipulator(req.arm_name)
                        if manip is None:
                            rospy.logerr('failed to find manipulator %s'%req.arm_name)
                            return None
                    else:
                        manips = [manip for manip in robot.GetManipulators() if manip.GetIkSolver() is not None and len(manip.GetArmIndices()) >= 6]
                        if len(manips) == 0:
                            rospy.logerr('failed to find manipulator end effector %s'%req.hand_frame_id)
                            return None
                        manip = manips[0]
                    robot.SetActiveManipulator(manip)

                    # create the target
                    target = env.GetKinBody(req.collision_object_name)
                    removetarget=False
                    if target is None:
                        target = CreateTarget(req.target)
                        removetarget = True
                    try:
                        res = object_manipulation_msgs.srv.GraspPlanningResponse()
                        # start planning
                        fastgrasping = FastGrasping(robot,target,ignoreik=options.ignoreik,returngrasps=options.returngrasps)
                        allgrasps,alljointvalues = fastgrasping.computeGrasp(graspparameters)
                        if allgrasps is not None and len(allgrasps) > 0:
                            res.error_code.value = object_manipulation_msgs.msg.GraspPlanningErrorCode.SUCCESS
                            for grasp,jointvalues in izip(allgrasps,alljointvalues):
                                rosgrasp = object_manipulation_msgs.msg.Grasp()
                                rosgrasp.pre_grasp_posture.header.stamp = rospy.Time.now()
                                rosgrasp.pre_grasp_posture.header.frame_id = options.mapframe
                                rosgrasp.pre_grasp_posture.name = [robot.GetJointFromDOFIndex(index).GetName() for index in fastgrasping.gmodel.manip.GetGripperIndices()]
                                rosgrasp.pre_grasp_posture.position = fastgrasping.gmodel.getPreshape(grasp)
                                # also include the arm positions
                                rosgrasp.grasp_posture.header = rosgrasp.pre_grasp_posture.header
                                rosgrasp.grasp_posture.name = rosgrasp.pre_grasp_posture.name + [robot.GetJointFromDOFIndex(index).GetName() for index in fastgrasping.gmodel.manip.GetArmIndices()]
                                rosgrasp.grasp_posture.position = jointvalues[r_[fastgrasping.gmodel.manip.GetGripperIndices(),fastgrasping.gmodel.manip.GetArmIndices()]]
                                rosgrasp.pre_grasp_posture.name = str(rosgrasp.pre_grasp_posture.name)
                                rosgrasp.grasp_posture.name = str(rosgrasp.grasp_posture.name)
                                T = fastgrasping.gmodel.getGlobalGraspTransform(grasp,collisionfree=True)
                                q = quatFromRotationMatrix(T[0:3,0:3])
                                rosgrasp.grasp_pose.position = geometry_msgs.msg.Point(T[0,3],T[1,3],T[2,3])
                                rosgrasp.grasp_pose.orientation = geometry_msgs.msg.Quaternion(q[1],q[2],q[3],q[0])
                                res.grasps.append(rosgrasp)
                                #indices = [robot.GetJoint(name).GetDOFIndex() for name in rosgrasp.grasp_posture.name]
                                #robot.SetDOFValues(rosgrasp.grasp_posture.position,indices)
                        else:
                            res.error_code.value = object_manipulation_msgs.msg.GraspPlanningErrorCode.OTHER_ERROR
                        rospy.loginfo('removing target %s'%target.GetName())
                        return res
                    finally:
                        with env:
                            if target is not None:
                                rospy.loginfo('removing target in finally %s'%target.GetName())
                                env.Remove(target)

        def SetGraspParameters(req):
            global graspparameters
            graspparameters = req
            res = orrosplanning.srv.SetGraspParametersResponse()
            return res

        sub = rospy.Subscriber("/joint_states", sensor_msgs.msg.JointState, UpdateRobotJoints,queue_size=1)
        s = rospy.Service('GraspPlanning', object_manipulation_msgs.srv.GraspPlanning, GraspPlanning)
        sparameters = rospy.Service('SetGraspParameters', orrosplanning.srv.SetGraspParameters, SetGraspParameters)
        print 'openrave %s service ready'%s.resolved_name

        # have to do this manually because running linkstatistics when viewer is enabled segfaults things
        if env.GetViewer() is None:
            if options._viewer is None:
                env.SetViewer('qtcoin')
            elif len(options._viewer) > 0:
                env.SetViewer(options._viewer)

        if options.ipython:
            from IPython.Shell import IPShellEmbed
            ipshell = IPShellEmbed(argv='',banner = 'Dropping into IPython',exit_msg = 'Leaving Interpreter, back to program.')
            ipshell(local_ns=locals())
        else:
            rospy.spin()
    finally:
        RaveDestroy()
