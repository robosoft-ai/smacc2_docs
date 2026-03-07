.. title:: Tutorial 4 — Navigation with Nav2 and Gazebo
.. meta::
   :description: Run sm_nav2_gazebo_test_1 to navigate a TurtleBot3 through waypoints in Gazebo using SMACC2, Nav2, and ClNav2Z.

Tutorial 4 — Navigation with Nav2 and Gazebo
=============================================

In this tutorial you will build and run ``sm_nav2_gazebo_test_1``, a state machine that drives a simulated TurtleBot3 through a sequence of waypoints using Nav2.

Prerequisites
-------------

- ROS 2 Jazzy with Nav2 and Gazebo packages installed:

.. code-block:: bash

   sudo apt install ros-jazzy-nav2-bringup ros-jazzy-turtlebot3-gazebo ros-jazzy-turtlebot3*

- SMACC2 cloned in your colcon workspace

|

Build
-----

.. code-block:: bash

   source /opt/ros/jazzy/setup.bash
   cd ~/ros2_ws
   colcon build --packages-select sm_nav2_gazebo_test_1
   source install/setup.bash

|

Run
---

In one terminal, launch the Gazebo simulation and Nav2:

.. code-block:: bash

   export TURTLEBOT3_MODEL=waffle
   ros2 launch nav2_bringup tb3_simulation_launch.py headless:=False

In a second terminal, launch the state machine:

.. code-block:: bash

   source ~/ros2_ws/install/setup.bash
   ros2 launch sm_nav2_gazebo_test_1 sm_nav2_gazebo_test_1.py

The robot will localize, navigate to two waypoints, rotate, and stop.

|

State Machine Overview
-----------------------

.. code-block:: text

   StAllSensorsGo → StSetInitialPose → StNavigateToWaypoint1 → StRotate → StNavigateToWaypoint2 → StFinalState

The state machine uses three orthogonals:

- **OrNavigation** — drives the robot using ``ClNav2Z``
- **OrTimer** — provides timeout events
- **OrKeyboard** — manual keyboard control fallback

The Navigation Orthogonal
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c++

   // orthogonals/or_navigation.hpp
   class OrNavigation : public smacc2::Orthogonal<OrNavigation>
   {
   public:
     void onInitialize() override
     {
       auto client = this->createClient<cl_nav2z::ClNav2Z>();
       client->createComponent<cl_nav2z::CpPose>(
           "/base_link", "/map");
       client->createComponent<cl_nav2z::CpOdomTracker>();
       client->createComponent<cl_nav2z::CpPlannerSwitcher>();
       client->createComponent<cl_nav2z::CpGoalCheckerSwitcher>();
       client->createComponent<cl_nav2z::CpAmcl>();
     }
   };

``ClNav2Z`` is a **component-based client**. Each component handles a specific concern:

.. list-table::
   :header-rows: 1

   * - Component
     - Purpose
   * - ``CpPose``
     - Robot pose from TF (base_link → map)
   * - ``CpOdomTracker``
     - Records odometry path for undo operations
   * - ``CpPlannerSwitcher``
     - Switches between planners and controllers at runtime
   * - ``CpGoalCheckerSwitcher``
     - Switches goal checker algorithms
   * - ``CpAmcl``
     - Sets initial pose for AMCL localization

Setting the Initial Pose
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c++

   // states/st_set_initial_pose.hpp
   struct StSetInitialPose : smacc2::SmaccState<StSetInitialPose, SmNav2GazeboTest1>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvCbSuccess<CbSetInitialPose, OrNavigation>, StNavigateToWaypoint1, SUCCESS>,
       Transition<EvCbFailure<CbSetInitialPose, OrNavigation>, StSetInitialPose, ABORT>,
       Transition<EvCbFailure<CbSetInitialPose, OrNavigation>, StFinalState, ABORT>
       >reactions;

     static void staticConfigure()
     {
       configure_orthogonal<OrNavigation, CbSetInitialPose>(
           -2.0, -0.5, 0.0);  // x, y, yaw
     }
   };

This state uses ``CbSetInitialPose`` to tell AMCL where the robot is on the map. On success it proceeds to the first waypoint. On failure it can retry or abort.

Navigating to a Waypoint
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c++

   // states/st_navigate_to_waypoint_1.hpp
   struct StNavigateToWaypoint1 : smacc2::SmaccState<StNavigateToWaypoint1, SmNav2GazeboTest1>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvActionSucceeded<ClNav2Z, OrNavigation>, StRotate, SUCCESS>,
       Transition<EvActionAborted<ClNav2Z, OrNavigation>, StFinalState, ABORT>
       >reactions;

     static void staticConfigure()
     {
       configure_orthogonal<OrNavigation, CbNavigateGlobalPosition>(
           2.0, 0.0, 0.0);  // x, y, yaw
     }
   };

``CbNavigateGlobalPosition`` sends a goal to Nav2's ``NavigateToPose`` action. The transition listens for ``EvActionSucceeded`` or ``EvActionAborted`` from the ``ClNav2Z`` client on ``OrNavigation``.

Rotating in Place
~~~~~~~~~~~~~~~~~~

.. code-block:: c++

   // states/st_rotate.hpp
   static void staticConfigure()
   {
     configure_orthogonal<OrNavigation, CbPureSpinning>(
         M_PI, 0.5);  // angle in radians, angular velocity
   }

``CbPureSpinning`` uses a custom local planner to rotate the robot 180 degrees at 0.5 rad/s.

|

Modifying Waypoints
-------------------

To change where the robot navigates, edit the coordinates in ``staticConfigure()``:

.. code-block:: c++

   // Navigate to a different position
   configure_orthogonal<OrNavigation, CbNavigateGlobalPosition>(
       5.0, 3.0, 1.57);  // x=5m, y=3m, yaw=90°

Rebuild and relaunch:

.. code-block:: bash

   colcon build --packages-select sm_nav2_gazebo_test_1
   source install/setup.bash
   ros2 launch sm_nav2_gazebo_test_1 sm_nav2_gazebo_test_1.py

|

Action Events
--------------

SMACC2 automatically generates events from ROS 2 action clients:

- ``EvActionSucceeded<ClNav2Z, OrNavigation>`` — goal completed successfully
- ``EvActionAborted<ClNav2Z, OrNavigation>`` — goal was aborted
- ``EvActionCancelled<ClNav2Z, OrNavigation>`` — goal was cancelled
- ``EvActionFeedback<ClNav2Z, OrNavigation>`` — feedback received (can be used for monitoring)

These events are parameterized by the **client type** and **orthogonal type**, so transitions are unambiguous even when multiple action clients are in use.

|

Summary
-------

You learned:

- How to use ``ClNav2Z`` with components for navigation
- How to configure waypoints with ``CbNavigateGlobalPosition``
- How action events (``EvActionSucceeded``, ``EvActionAborted``) drive transitions
- How to modify waypoints and rebuild

|

Next Steps
----------

In :doc:`tutorial-5-client-behaviors` you will learn how to write your own client behaviors, both synchronous and asynchronous.
