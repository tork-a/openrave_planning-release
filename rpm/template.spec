Name:           ros-indigo-openrave
Version:        0.0.5
Release:        1%{?dist}
Summary:        ROS openrave package

Group:          Development/Libraries
License:        Lesser GPL and Apache License
URL:            http://openrave.org
Source0:        %{name}-%{version}.tar.gz

Requires:       SoQt-devel
Requires:       assimp-devel
Requires:       boost-devel
Requires:       bullet-devel
Requires:       collada-dom-devel
Requires:       ffmpeg-devel
Requires:       glew-devel
Requires:       h5py
Requires:       lapack-devel
Requires:       libogg-devel
Requires:       numpy
Requires:       ode
Requires:       pcre-devel
Requires:       python-devel
Requires:       python-ipython
Requires:       qhull-devel
Requires:       qt
Requires:       ros-indigo-collada-robots
Requires:       ros-indigo-std-msgs
Requires:       scipy
Requires:       sympy
Requires:       x264-devel
Requires:       zlib-devel
BuildRequires:  SoQt-devel
BuildRequires:  assimp-devel
BuildRequires:  boost-devel
BuildRequires:  bullet-devel
BuildRequires:  collada-dom-devel
BuildRequires:  ffmpeg-devel
BuildRequires:  git
BuildRequires:  glew-devel
BuildRequires:  h5py
BuildRequires:  lapack-devel
BuildRequires:  libogg-devel
BuildRequires:  numpy
BuildRequires:  ode
BuildRequires:  pcre-devel
BuildRequires:  python-devel
BuildRequires:  python-ipython
BuildRequires:  qhull-devel
BuildRequires:  qt
BuildRequires:  ros-indigo-catkin
BuildRequires:  ros-indigo-collada-robots
BuildRequires:  ros-indigo-std-msgs
BuildRequires:  scipy
BuildRequires:  sympy
BuildRequires:  x264-devel
BuildRequires:  zlib-devel

%description
In order to use, please add the following line in your bashrc:

%prep
%setup -q

%build
# In case we're installing to a non-standard location, look for a setup.sh
# in the install tree that was dropped by catkin, and source it.  It will
# set things like CMAKE_PREFIX_PATH, PKG_CONFIG_PATH, and PYTHONPATH.
if [ -f "/opt/ros/indigo/setup.sh" ]; then . "/opt/ros/indigo/setup.sh"; fi
mkdir -p obj-%{_target_platform} && cd obj-%{_target_platform}
%cmake .. \
        -UINCLUDE_INSTALL_DIR \
        -ULIB_INSTALL_DIR \
        -USYSCONF_INSTALL_DIR \
        -USHARE_INSTALL_PREFIX \
        -ULIB_SUFFIX \
        -DCMAKE_INSTALL_LIBDIR="lib" \
        -DCMAKE_INSTALL_PREFIX="/opt/ros/indigo" \
        -DCMAKE_PREFIX_PATH="/opt/ros/indigo" \
        -DSETUPTOOLS_DEB_LAYOUT=OFF \
        -DCATKIN_BUILD_BINARY_PACKAGE="1" \

make %{?_smp_mflags}

%install
# In case we're installing to a non-standard location, look for a setup.sh
# in the install tree that was dropped by catkin, and source it.  It will
# set things like CMAKE_PREFIX_PATH, PKG_CONFIG_PATH, and PYTHONPATH.
if [ -f "/opt/ros/indigo/setup.sh" ]; then . "/opt/ros/indigo/setup.sh"; fi
cd obj-%{_target_platform}
make %{?_smp_mflags} install DESTDIR=%{buildroot}

%files
/opt/ros/indigo

%changelog
* Wed Feb 15 2017 Kei Okada <k-okada@jsk.t.u-tokyo.ac.jp> - 0.0.5-1
- Autogenerated by Bloom

* Fri Feb 03 2017 Kei Okada <k-okada@jsk.t.u-tokyo.ac.jp> - 0.0.5-0
- Autogenerated by Bloom

* Thu Jan 19 2017 Kei Okada <k-okada@jsk.t.u-tokyo.ac.jp> - 0.0.4-0
- Autogenerated by Bloom

* Fri May 27 2016 Kei Okada <k-okada@jsk.t.u-tokyo.ac.jp> - 0.0.3-0
- Autogenerated by Bloom

* Wed May 25 2016 Kei Okada <k-okada@jsk.t.u-tokyo.ac.jp> - 0.0.2-0
- Autogenerated by Bloom

* Wed May 25 2016 Kei Okada <k-okada@jsk.t.u-tokyo.ac.jp> - 0.0.1-0
- Autogenerated by Bloom

