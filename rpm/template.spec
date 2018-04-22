Name:           ros-kinetic-collada-robots
Version:        0.0.6
Release:        0%{?dist}
Summary:        ROS collada_robots package

Group:          Development/Libraries
License:        T.D.B
URL:            http://www.openrave.org/en/main/robots.html
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  git
BuildRequires:  ros-kinetic-catkin
BuildRequires:  unzip

%description
COLLADA 1.5 Robot Models Repository This repository is associated with the Open
Robotics Automation Virtual Environment (OpenRAVE). The open and view them,
install OpenRAVE and execute: openrave XXX.zae The robots are augmented with
information as described by the &quot;OpenRAVE&quot; profile here:
http://openrave.programmingvision.com/index.php/Started:COLLADA *.zae files are
zip archives which contain the raw collada 1.5 xml (dae).

%prep
%setup -q

%build
# In case we're installing to a non-standard location, look for a setup.sh
# in the install tree that was dropped by catkin, and source it.  It will
# set things like CMAKE_PREFIX_PATH, PKG_CONFIG_PATH, and PYTHONPATH.
if [ -f "/opt/ros/kinetic/setup.sh" ]; then . "/opt/ros/kinetic/setup.sh"; fi
mkdir -p obj-%{_target_platform} && cd obj-%{_target_platform}
%cmake .. \
        -UINCLUDE_INSTALL_DIR \
        -ULIB_INSTALL_DIR \
        -USYSCONF_INSTALL_DIR \
        -USHARE_INSTALL_PREFIX \
        -ULIB_SUFFIX \
        -DCMAKE_INSTALL_LIBDIR="lib" \
        -DCMAKE_INSTALL_PREFIX="/opt/ros/kinetic" \
        -DCMAKE_PREFIX_PATH="/opt/ros/kinetic" \
        -DSETUPTOOLS_DEB_LAYOUT=OFF \
        -DCATKIN_BUILD_BINARY_PACKAGE="1" \

make %{?_smp_mflags}

%install
# In case we're installing to a non-standard location, look for a setup.sh
# in the install tree that was dropped by catkin, and source it.  It will
# set things like CMAKE_PREFIX_PATH, PKG_CONFIG_PATH, and PYTHONPATH.
if [ -f "/opt/ros/kinetic/setup.sh" ]; then . "/opt/ros/kinetic/setup.sh"; fi
cd obj-%{_target_platform}
make %{?_smp_mflags} install DESTDIR=%{buildroot}

%files
/opt/ros/kinetic

%changelog
* Sun Apr 22 2018 Kei Okada <k-okada@jsk.t.u-tokyo.ac.jp> - 0.0.6-0
- Autogenerated by Bloom

