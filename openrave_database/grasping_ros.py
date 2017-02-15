#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Rosen Diankov
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
"""
To execute on 8 cores of the current localhost, first store roscore and then run:

.. code-block:: bash

  roscd openrave_database; rosrun parallel_util workmanagerlauncher.py --module=grasping_ros --launchservice='8*localhost'

For more options run:

.. code-block:: bash

  rosrun parallel_util workmanagerlauncher.py --help

"""

from __future__ import with_statement # for python 2.5

PKG = 'openrave_database' # ROS package name for dependencies
import roslib; roslib.load_manifest(PKG)

from numpy import *
import numpy
import sys, time
from optparse import OptionParser
from openravepy import *
from openravepy.databases import grasping

model = producer = consumer = gatherer = produceriter = None
producercount = 0
def start(args=None):
    global model, producer, consumer, gatherer
    try:
        options,model = grasping.GraspingModel.InitializeFromParser(args=args)
        producer, consumer, gatherer, num = model.generatepcg(*model.autogenerateparams(options))
    except Exception, e:
        print e
        print 'faile with args: ',args
    print 'total jobs: ',num
    
def service_start(args):
    start(args)
    
def service_processrequest(*args):
    global consumer
    return consumer(*args)

def server_processresponse(*args):
    global gatherer
    if len(args) > 0:
        gatherer(*args)

def server_requestwork():
    global producer, produceriter,producercount
    try:
        print 'grasping ',producercount
        producercount += 1
        if produceriter is None:
            produceriter=producer()
        return produceriter.next()
    except:
        return None

def server_start(args):
    global producercount
    start(args)
    producercount = 0

def server_end():
    global model, gatherer
    gatherer()
    model.save()

def launcher_start(args):
    start(args)
    return ''
