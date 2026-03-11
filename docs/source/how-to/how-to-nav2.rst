.. title:: How to Use Nav2 with SMACC2
.. meta::
   :description: Complete guide for using the ClNav2Z client library with SMACC2 for autonomous navigation — getting started, library tour, and usage patterns including writing custom behaviors and components.

How to Use Nav2 with SMACC2
============================

Getting Started
----------------

Required Installations
~~~~~~~~~~~~~~~~~~~~~~~

**ROS 2 Jazzy**

.. code-block:: bash

   # Follow https://docs.ros.org/en/jazzy/Installation.html
   sudo apt install ros-jazzy-desktop

**Nav2 Stack**

.. code-block:: bash

   sudo apt install ros-jazzy-nav2-bringup ros-jazzy-nav2-simple-commander

**Gazebo Simulation with TurtleBot3**

.. code-block:: bash

   sudo apt install ros-jazzy-turtlebot3-gazebo
   export TURTLEBOT3_MODEL=waffle

**Map File** for localization (or SLAM Toolbox running for online mapping)

Assembling the Workspace
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src

   # SMACC2 framework and client libraries
   git clone https://github.com/robosoft-ai/SMACC2.git -b jazzy

The packages you need are:

- ``smacc2`` — core state machine framework
- ``smacc2_msgs`` — SMACC2 message definitions
- ``cl_nav2z`` — Nav2 client library (inside ``SMACC2/smacc2_client_library/cl_nav2z/``)
- ``sm_nav2_gazebo_test_1`` — reference state machine (inside ``SMACC2/smacc2_sm_reference_library/``)
- Nav2 custom planners (inside ``SMACC2/smacc2_client_library/cl_nav2z/custom_planners/``)

Building the Workspace
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd ~/ros2_ws
   source /opt/ros/jazzy/setup.bash
   colcon build --packages-select cl_nav2z sm_nav2_gazebo_test_1
   source install/setup.bash

.. note::

   You can also use ``colcon build --packages-up-to sm_nav2_gazebo_test_1``
   to build only the required dependency chain.

Launching the Application
~~~~~~~~~~~~~~~~~~~~~~~~~~

You need **two terminals**. Source the workspace in each:

.. code-block:: bash

   source ~/ros2_ws/install/setup.bash

**Terminal 1 — Nav2 + Gazebo Simulation**

.. code-block:: bash

   export TURTLEBOT3_MODEL=waffle
   ros2 launch nav2_bringup tb3_simulation_launch.py headless:=False

**Terminal 2 — State Machine**

.. code-block:: bash

   source ~/ros2_ws/install/setup.bash
   ros2 launch sm_nav2_gazebo_test_1 sm_nav2_gazebo_test_1.py

The state machine executes this mission automatically:

.. code-block:: text

   WaitNav2Ready → SetInitialPose → Navigate(2.0, 0.0) → Rotate(π) → Navigate(0.0, 0.0) → Done

Monitor with:

.. code-block:: bash

   # Current state
   ros2 topic echo /sm_nav2_gazebo_test_1/smacc/status

   # Transition log
   ros2 topic echo /sm_nav2_gazebo_test_1/smacc/transition_log

For a more complex workspace assembly example involving IsaacSim and NVIDIA
Isaac ROS, see the
`sm_nav2_test_7 README <https://github.com/robosoft-ai/nova_carter_sm_library/tree/jazzy/sm_nav2_test_7>`_.

Tour of the Nav2 Client Behavior Library
------------------------------------------

The ``cl_nav2z`` client library integrates Nav2 with SMACC2 for autonomous
navigation. It wraps the ``NavigateToPose`` action client and provides
components for pose tracking, odometry recording, planner switching, and more.

For the full API reference, see the
`cl_nav2z source <https://github.com/robosoft-ai/SMACC2/tree/jazzy/smacc2_client_library/cl_nav2z>`_.

Folder Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

   cl_nav2z/
   ├── cl_nav2z/
   │   ├── include/cl_nav2z/
   │   │   ├── cl_nav2z.hpp                        # Client
   │   │   ├── client_behaviors.hpp                 # Behavior includes
   │   │   ├── common.hpp
   │   │   ├── client_behaviors/
   │   │   │   ├── cb_navigate_global_position.hpp
   │   │   │   ├── cb_navigate_forward.hpp
   │   │   │   ├── cb_navigate_backwards.hpp
   │   │   │   ├── cb_rotate.hpp
   │   │   │   ├── cb_absolute_rotate.hpp
   │   │   │   ├── cb_pure_spinning.hpp
   │   │   │   ├── cb_undo_path_backwards.hpp
   │   │   │   ├── cb_abort_navigation.hpp
   │   │   │   ├── cb_wait_nav2_nodes.hpp
   │   │   │   ├── cb_wait_pose.hpp
   │   │   │   ├── cb_wait_transform.hpp
   │   │   │   ├── cb_pause_slam.hpp
   │   │   │   ├── cb_resume_slam.hpp
   │   │   │   ├── cb_save_slam_map.hpp
   │   │   │   └── ... (additional behaviors)
   │   │   └── components/
   │   │       ├── nav2_action_interface/cp_nav2_action_interface.hpp
   │   │       ├── pose/cp_pose.hpp
   │   │       ├── odom_tracker/cp_odom_tracker.hpp
   │   │       ├── planner_switcher/cp_planner_switcher.hpp
   │   │       ├── goal_checker_switcher/cp_goal_checker_switcher.hpp
   │   │       ├── amcl/cp_amcl.hpp
   │   │       ├── slam_toolbox/cp_slam_toolbox.hpp
   │   │       ├── costmap_switch/cp_costmap_switch.hpp
   │   │       └── waypoints_navigator/
   │   │           ├── cp_waypoints_navigator.hpp
   │   │           ├── cp_waypoints_navigator_base.hpp
   │   │           ├── cp_waypoints_event_dispatcher.hpp
   │   │           └── cp_waypoints_visualizer.hpp
   │   ├── src/cl_nav2z/
   │   │   ├── cl_nav2z.cpp
   │   │   ├── client_behaviors/
   │   │   │   └── ... (matching .cpp files)
   │   │   └── components/
   │   │       └── ... (matching .cpp files)
   │   ├── CMakeLists.txt
   │   └── package.xml
   └── custom_planners/
       ├── forward_global_planner/
       ├── forward_local_planner/
       ├── backward_global_planner/
       ├── backward_local_planner/
       ├── pure_spinning_local_planner/
       ├── undo_path_global_planner/
       └── nav2z_planners_common/

Components
~~~~~~~~~~~

``ClNav2Z`` creates 2 core components internally. Additional components are
created at the orthogonal level:

.. code-block:: c++

   // Created internally by ClNav2Z
   ClNav2Z(std::string actionServerName = "/navigate_to_pose");

   template <typename TOrthogonal, typename TClient>
   void onComponentInitialization()
   {
     this->createComponent<
       smacc2::client_core_components::CpActionClient<
         nav2_msgs::action::NavigateToPose>,
       TOrthogonal, ClNav2Z>(actionServerName_);

     this->createComponent<
       components::CpNav2ActionInterface, TOrthogonal, ClNav2Z>();
   }

.. list-table::
   :header-rows: 1

   * - Component
     - Purpose
     - Key Methods / Signals
   * - ``CpNav2ActionInterface``
     - Nav2 action client wrapper
     - ``sendNavigationGoal()``, ``cancelNavigation()`` / Signals: ``onNavigationSucceeded_``, ``onNavigationAborted_``
   * - ``CpPose``
     - Robot pose from TF
     - ``toPoseStampedMsg()``, ``getYaw()``, ``getX()``, ``getY()``
   * - ``CpOdomTracker``
     - Record/playback odometry paths
     - ``pushPath()``, ``popPath()``, ``clearPath()``, ``setWorkingMode()``
   * - ``CpPlannerSwitcher``
     - Switch planners/controllers at runtime
     - ``setForwardPlanner()``, ``setBackwardPlanner()``, ``setPureSpinningPlanner()``
   * - ``CpGoalCheckerSwitcher``
     - Switch goal checker algorithms
     - ``setGoalCheckerId()``, ``setDefaultGoalChecker()``
   * - ``CpAmcl``
     - Set initial pose for AMCL
     - ``setInitialPose()``
   * - ``CpSlamToolbox``
     - SLAM state management
     - ``toggleState()``, ``getState()``
   * - ``CpWaypointNavigator``
     - Multi-waypoint orchestration
     - ``sendNextGoal()``, ``loadWayPointsFromFile()``, ``rewind()``, ``forward()``
   * - ``CpCostmapSwitch``
     - Enable/disable costmap layers
     - ``enable()``, ``disable()``

Behaviors
~~~~~~~~~~

Navigation Behaviors
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Behavior
     - Constructor Parameters
     - Description
   * - ``CbNavigateGlobalPosition``
     - ``x``, ``y``, ``yaw``, optional ``CbNavigateGlobalPositionOptions``
     - Navigate to map coordinates
   * - ``CbNavigateForward``
     - ``forwardDistance`` (float)
     - Drive forward a specified distance
   * - ``CbNavigateBackwards``
     - ``backwardDistance`` (float)
     - Drive backward a specified distance
   * - ``CbNavigateNamedWaypoint``
     - ``waypointName`` (string)
     - Navigate to a named waypoint
   * - ``CbNavigateNextWaypoint``
     - optional ``NavigateNextWaypointOptions``
     - Navigate to the next waypoint in sequence
   * - ``CbUndoPathBackwards``
     - (none)
     - Retrace recorded odometry path in reverse
   * - ``CbAbortNavigation``
     - (none)
     - Cancel current navigation goal (sync)

Rotation Behaviors
^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Behavior
     - Constructor Parameters
     - Description
   * - ``CbRotate``
     - ``rotateDegree`` (float), optional ``SpinningPlanner``
     - Rotate in place by a relative angle
   * - ``CbAbsoluteRotate``
     - ``targetYaw`` (float)
     - Rotate to an absolute yaw
   * - ``CbPureSpinning``
     - ``yawTarget`` (float), ``angularVelocity`` (float)
     - Pure spinning rotation
   * - ``CbRotateLookAt``
     - ``targetPose`` (PoseStamped)
     - Rotate to face a target pose
   * - ``CbSpiralMotion``
     - spiral search parameters
     - Spiral search pattern

Monitoring Behaviors
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Behavior
     - Constructor Parameters
     - Description
   * - ``CbWaitNav2Nodes``
     - optional ``std::vector<Nav2Nodes>``
     - Wait for Nav2 nodes to be available
   * - ``CbWaitPose``
     - (none)
     - Wait for robot pose to be available
   * - ``CbWaitTransform``
     - ``sourceFrame``, ``targetFrame``
     - Wait for a TF transform to be available

SLAM Behaviors
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Behavior
     - Constructor Parameters
     - Description
   * - ``CbPauseSlam``
     - optional ``serviceName``
     - Pause SLAM Toolbox measurements
   * - ``CbResumeSlam``
     - optional ``serviceName``
     - Resume SLAM Toolbox measurements
   * - ``CbSaveSlamMap``
     - ``mapPath`` (string)
     - Save the current SLAM map

All async behaviors post ``EvCbSuccess`` on completion and ``EvCbFailure``
on error. Nav2 action behaviors also post ``EvActionSucceeded``,
``EvActionAborted``, and ``EvActionCancelled``.

Using the Nav2 Client Behavior Library
----------------------------------------

Configuring the Orthogonal
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create an orthogonal that instantiates the ``ClNav2Z`` client and adds
the components you need. Unlike ``ClPx4Mr``, most Nav2 components are
created at the orthogonal level:

.. code-block:: c++

   #include <cl_nav2z/cl_nav2z.hpp>

   class OrNavigation : public smacc2::Orthogonal<OrNavigation>
   {
   public:
     void onInitialize() override
     {
       auto client = this->createClient<cl_nav2z::ClNav2Z>();

       // Robot pose from TF (base_link in map frame)
       client->createComponent<cl_nav2z::CpPose>("base_link", "map");

       // Odometry path tracking for undo operations
       client->createComponent<cl_nav2z::odom_tracker::CpOdomTracker>();

       // Runtime planner/controller switching
       client->createComponent<cl_nav2z::CpPlannerSwitcher>();

       // Runtime goal checker switching
       client->createComponent<cl_nav2z::CpGoalCheckerSwitcher>();

       // AMCL initial pose setting
       client->createComponent<cl_nav2z::CpAmcl>();
     }
   };

Register the orthogonal in your state machine's ``onInitialize()``:

.. code-block:: c++

   struct SmMyNavMission
     : smacc2::SmaccStateMachineBase<SmMyNavMission, StInitial>
   {
     void onInitialize() override
     {
       this->createOrthogonal<OrNavigation>();
     }
   };

Using a Behavior
~~~~~~~~~~~~~~~~~

Behaviors are configured in a state's ``staticConfigure()`` using
``configure_orthogonal<>``. Constructor parameters are passed as arguments.
The behavior executes asynchronously on state entry and posts events
that drive transitions:

.. code-block:: c++

   #include <cl_nav2z/client_behaviors/cb_navigate_global_position.hpp>

   struct StNavigateToWaypoint1
     : smacc2::SmaccState<StNavigateToWaypoint1, SmMyNavMission>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<smacc2::EvActionSucceeded<ClNav2Z, OrNavigation>,
                  StRotate, SUCCESS>,
       Transition<smacc2::EvActionAborted<ClNav2Z, OrNavigation>,
                  StFinalState, ABORT>
     > reactions;

     static void staticConfigure()
     {
       configure_orthogonal<OrNavigation, CbNavigateGlobalPosition>(
           2.0, 0.0, 0.0);
     }
   };

The pattern is the same for all Nav2 behaviors — change the behavior class
and its parameters:

.. code-block:: c++

   // Rotate in place using a pure spinning planner
   configure_orthogonal<OrNavigation, CbPureSpinning>(M_PI, 0.5);

   // Navigate forward 3 meters
   configure_orthogonal<OrNavigation, CbNavigateForward>(3.0f);

   // Retrace the recorded odometry path in reverse
   configure_orthogonal<OrNavigation, CbUndoPathBackwards>();

   // Wait for Nav2 nodes before starting navigation
   configure_orthogonal<OrNavigation, CbWaitNav2Nodes>();

Planner Presets
^^^^^^^^^^^^^^^^

``CpPlannerSwitcher`` provides preset methods for common navigation patterns:

.. list-table::
   :header-rows: 1

   * - Method
     - Use Case
   * - ``setForwardPlanner()``
     - Standard forward navigation
   * - ``setBackwardPlanner()``
     - Reverse navigation
   * - ``setPureSpinningPlanner()``
     - In-place rotation
   * - ``setUndoPathBackwardPlanner()``
     - Retracing recorded odometry paths
   * - ``setDefaultPlanners()``
     - Restore original planner configuration

Writing Your Own Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~

To add a new navigation behavior, create a class that inherits from
``CbNav2ZClientBehaviorBase`` (which extends ``SmaccAsyncClientBehavior``
with Nav2-specific helpers), acquires the components it needs, and posts
events when done.

Here is a complete example — a behavior that navigates to a position and
then rotates to face a specified heading:

**Header** (``include/cl_nav2z/client_behaviors/cb_navigate_and_orient.hpp``):

.. code-block:: c++

   #pragma once

   #include <cl_nav2z/client_behaviors/cb_nav2z_client_behavior_base.hpp>

   namespace cl_nav2z
   {

   class CbNavigateAndOrient : public CbNav2ZClientBehaviorBase
   {
   public:
     CbNavigateAndOrient(float x, float y, float finalYaw);

     void onEntry() override;
     void onExit() override;

   private:
     float x_, y_, finalYaw_;
   };

   }  // namespace cl_nav2z

**Source** (``src/cl_nav2z/client_behaviors/cb_navigate_and_orient.cpp``):

.. code-block:: c++

   #include <cl_nav2z/client_behaviors/cb_navigate_and_orient.hpp>
   #include <cl_nav2z/components/nav2_action_interface/cp_nav2_action_interface.hpp>

   namespace cl_nav2z
   {

   CbNavigateAndOrient::CbNavigateAndOrient(
     float x, float y, float finalYaw)
   : x_(x), y_(y), finalYaw_(finalYaw)
   {
   }

   void CbNavigateAndOrient::onEntry()
   {
     // Acquire the Nav2 action interface component
     cl_nav2z::components::CpNav2ActionInterface * navInterface;
     this->requiresComponent(navInterface);

     // Build the navigation goal with target orientation
     geometry_msgs::msg::PoseStamped goal;
     goal.header.frame_id = "map";
     goal.pose.position.x = x_;
     goal.pose.position.y = y_;
     goal.pose.orientation.z = std::sin(finalYaw_ / 2.0);
     goal.pose.orientation.w = std::cos(finalYaw_ / 2.0);

     navInterface->sendNavigationGoal(goal);
   }

   void CbNavigateAndOrient::onExit() {}

   }  // namespace cl_nav2z

The key steps for any custom Nav2 behavior:

1. **Inherit from** ``CbNav2ZClientBehaviorBase`` for Nav2-specific helpers
2. **Acquire components** with ``requiresComponent()`` in ``onEntry()``
3. **Send goals** through ``CpNav2ActionInterface``
4. The action client events (``EvActionSucceeded``, ``EvActionAborted``)
   are posted automatically by the framework

Writing Your Own Component
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Components manage ROS 2 communication and expose methods and signals for
behaviors to use. Write a new component when you need to:

- Monitor a topic not covered by existing components (e.g., costmap updates)
- Add reusable computation that multiple behaviors share
- Provide runtime-switchable configuration

A component inherits from ``ISmaccComponent`` and optionally from
``ISmaccUpdatable`` for periodic updates.

Here is a complete example — a component that monitors the robot's velocity:

**Header** (``include/cl_nav2z/components/velocity_monitor/cp_velocity_monitor.hpp``):

.. code-block:: c++

   #pragma once

   #include <smacc2/smacc.hpp>
   #include <nav_msgs/msg/odometry.hpp>

   namespace cl_nav2z
   {

   class CpVelocityMonitor : public smacc2::ISmaccComponent
   {
   public:
     CpVelocityMonitor();
     virtual ~CpVelocityMonitor();

     void onInitialize() override;

     double getLinearVelocity() const;
     double getAngularVelocity() const;

     smacc2::SmaccSignal<void()> onStopped_;

   private:
     void onOdomReceived(const nav_msgs::msg::Odometry & msg);

     rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr sub_;
     double linearVelocity_ = 0.0;
     double angularVelocity_ = 0.0;
   };

   }  // namespace cl_nav2z

**Source** (``src/cl_nav2z/components/velocity_monitor/cp_velocity_monitor.cpp``):

.. code-block:: c++

   #include <cl_nav2z/components/velocity_monitor/cp_velocity_monitor.hpp>

   namespace cl_nav2z
   {

   CpVelocityMonitor::CpVelocityMonitor() {}
   CpVelocityMonitor::~CpVelocityMonitor() {}

   void CpVelocityMonitor::onInitialize()
   {
     auto node = this->getNode();
     sub_ = node->create_subscription<nav_msgs::msg::Odometry>(
       "/odom", rclcpp::SensorDataQoS(),
       std::bind(&CpVelocityMonitor::onOdomReceived, this,
                 std::placeholders::_1));
   }

   void CpVelocityMonitor::onOdomReceived(
     const nav_msgs::msg::Odometry & msg)
   {
     linearVelocity_ = msg.twist.twist.linear.x;
     angularVelocity_ = msg.twist.twist.angular.z;

     if (std::abs(linearVelocity_) < 0.01 &&
         std::abs(angularVelocity_) < 0.01)
     {
       onStopped_();
     }
   }

   double CpVelocityMonitor::getLinearVelocity() const
   { return linearVelocity_; }

   double CpVelocityMonitor::getAngularVelocity() const
   { return angularVelocity_; }

   }  // namespace cl_nav2z

Add the component at the orthogonal level:

.. code-block:: c++

   client->createComponent<cl_nav2z::CpVelocityMonitor>();

**When to write a component vs. putting logic in a behavior:**

.. list-table::
   :header-rows: 1

   * - Criterion
     - Component
     - Behavior
   * - Lifetime
     - State machine scoped (lives as long as the client)
     - State scoped (created/destroyed with each state)
   * - Reusability
     - Shared across multiple behaviors
     - Single-purpose per state
   * - ROS 2 I/O
     - Owns publishers/subscribers
     - Uses components for I/O
   * - Signals
     - Emits signals for behaviors to connect to
     - Connects to component signals, posts state machine events
