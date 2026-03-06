.. title:: Getting Started
.. meta::
   :description: Naming conventions, folder structures, and setup instructions for getting started with the SMACC2 state machine library for ROS2.

Getting Started
===============

Install ROS 2
--------------

SMACC2 targets **ROS 2 Jazzy** on Ubuntu 24.04. Follow the official installation guide:

- `ROS 2 Jazzy Installation <https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html>`_

After installing, source the setup file:

.. code-block:: bash

   source /opt/ros/jazzy/setup.bash

Install SMACC2
----------------

Create a ROS 2 workspace:

.. code-block:: bash

   mkdir -p ~/ros2_ws/src

Clone the SMACC2 repository:

.. code-block:: bash

   cd ~/ros2_ws/src
   git clone https://github.com/robosoft-ai/SMACC2.git

Install dependencies:

.. code-block:: bash

   cd ~/ros2_ws
   rosdep install --from-paths src --ignore-src -r -y

Build:

.. code-block:: bash

   colcon build

Source the workspace after the build completes:

.. code-block:: bash

   source ~/ros2_ws/install/setup.bash

Download the SMACC Viewer (RTA)
---------------------------------

The SMACC Runtime Analyzer (RTA) is a graphical tool for real-time visualization and debugging of SMACC2 state machines. Download and install instructions are available at:

- `SMACC Viewer Installation <https://robosoft.ai/viewer>`_

|
|

Naming Convention
-----------------

Because of the complexities of c++ template code and state machines in general, the Authors of the SMACC library developed a naming convention that users are strongly encouraged to follow.
**Benefits of Adopting the Convention**

The first benefit, is that the convention greatly improves code readability, especially from inside an IDE or the SMACC doxygen pages.

The second benefit, is that if you run into issues, the SMACC support team can quickly and easily get a handle on the broader picture of your problem.

And the third benefit, is that the SMACC development tools, such as the SMACC Viewer and the yet-to-be-built code-generator will utilize this same naming convention and by adopting it, you ensure compatibility.
**Prefixes**

Header files have the following format…

- ``sm_`` = state machine (ex: sm_dance_bot.h)
- ``ms_`` = mode state (ex: ms_recover.h)
- ``ss_`` = super state (ex: ss_sequence_1.h)
- ``st_`` = state (ex: st_navigate_to_waypoints_x.h)
- ``sti_`` = inner state (ex: sti_radial_rotate.h)
- ``sr_`` = state reactor (ex: sr_all_events_go.h)
- ``or_`` = orthogonal (ex: or_navigation.h)
- ``cl_`` = client (ex: cl_move_base_z.h)
- ``cb_`` = client behavior (ex: cb_timeout_watchdog.h)
- ``cp_`` = component (ex: cp_odom_tracker.h)
- ``ev_`` = event (ex: ev_navigation_success.h)

And then classes have the following format…

- Sm = state machine (ex: SmDanceBot)
- Ms = mode state (ex: MsRecover)
- Ss = super state (ex: SsSequence1)
- St = state (ex: StNavigateToWaypointsX)
- Sti = inner state (ex: StiRadialRotate)
- Sr = state reactor (ex: SrAllEventsGo)
- Or = orthogonal (ex: OrNavigation)
- Cl = client (ex: ClMoveBaseZ)
- Cb = client behavior (ex: CbTimeoutWatchdog)
- Cp = component (ex: CpOdomTracker)
- Ev = event (ex: EvNavigationSuccess)

|
|

State Machine Folder Structure
------------------------------

**Example State Machine Folder Structure**

.. code-block:: text

   sm_example/
   ├── CMakeLists.txt
   ├── package.xml
   ├── config/
   ├── docs/
   ├── include/
   │   └── sm_example/
   │       ├── orthogonals/
   │       │   └── or_navigation.hpp
   │       ├── states/
   │       │   ├── st_state_1.hpp
   │       │   └── st_state_2.hpp
   │       ├── superstates/
   │       │   └── ss_superstate_1.hpp
   │       ├── modestates/
   │       │   └── ms_run_mode.hpp
   │       └── sm_example.hpp
   ├── launch/
   │   └── sm_example.launch.py
   └── src/
       └── sm_example/
           └── sm_example_node.cpp

The ``include/sm_example/sm_example.hpp`` header is the main state machine definition, and ``src/sm_example/sm_example_node.cpp`` contains the ``main()`` entry point.

|
|

Client Library Folder Structure
-------------------------------

**Example Client Library Folder Structure**

.. code-block:: text

   cl_example/
   ├── CMakeLists.txt
   ├── package.xml
   ├── include/
   │   └── cl_example/
   │       ├── cl_example.hpp
   │       ├── client_behaviors/
   │       │   ├── cb_behavior_1.hpp
   │       │   └── cb_behavior_2.hpp
   │       └── components/
   │           ├── cp_component_1.hpp
   │           └── cp_component_2.hpp
   └── src/
       └── cl_example/
           ├── cl_example.cpp
           ├── client_behaviors/
           │   ├── cb_behavior_1.cpp
           │   └── cb_behavior_2.cpp
           └── components/
               ├── cp_component_1.cpp
               └── cp_component_2.cpp

The client library compiles into a shared library (``.so``) that state machines link against at build time.


