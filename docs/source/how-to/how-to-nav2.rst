.. title:: How to Use Nav2 with SMACC2
.. meta::
   :description: Reference guide for using the ClNav2Z client library with SMACC2 for autonomous navigation — components, behaviors, prerequisites, and example missions.

How to Use Nav2 with SMACC2
============================

The ``cl_nav2z`` client library integrates Nav2 with SMACC2 for autonomous navigation. This guide covers the client, its components, behaviors, and a complete example mission.

Getting Started
----------------

1. **Nav2 stack** installed:

.. code-block:: bash

   sudo apt install ros-jazzy-nav2-bringup ros-jazzy-nav2-simple-commander

2. **Gazebo simulation** with a robot (e.g., TurtleBot3):

.. code-block:: bash

   sudo apt install ros-jazzy-turtlebot3-gazebo
   export TURTLEBOT3_MODEL=waffle

3. **Map file** for localization (or SLAM Toolbox running for online mapping)

4. **cl_nav2z** and ``sm_nav2_gazebo_test_1`` built in your colcon workspace

Overview
--------

``ClNav2Z`` is a **pure orchestrator client** — it creates 2 core components during orthogonal initialization, and additional components are created at the orthogonal level:

.. code-block:: c++

   // ClNav2Z constructor
   ClNav2Z(std::string actionServerName = "/navigate_to_pose");

   // Component composition during orthogonal initialization
   template <typename TOrthogonal, typename TClient>
   void onComponentInitialization()
   {
     // Core action client component
     this->createComponent<
       smacc2::client_core_components::CpActionClient<
         nav2_msgs::action::NavigateToPose>,
       TOrthogonal, ClNav2Z>(actionServerName_);

     // Nav2-specific interface component
     this->createComponent<
       components::CpNav2ActionInterface, TOrthogonal, ClNav2Z>();
   }

Additional components (``CpPose``, ``CpOdomTracker``, ``CpPlannerSwitcher``, etc.) are created at the orthogonal level — see `Orthogonal Setup`_ below.

Reference state machine: ``sm_nav2_gazebo_test_1``

Components
----------

.. list-table::
   :header-rows: 1

   * - Component
     - Purpose
     - Key Methods/Signals
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

Navigation Behaviors
---------------------

.. list-table::
   :header-rows: 1

   * - Behavior
     - Type
     - Constructor Parameters
   * - ``CbNavigateGlobalPosition``
     - Async
     - ``x``, ``y``, ``yaw``, optional ``CbNavigateGlobalPositionOptions``
   * - ``CbNavigateForward``
     - Async
     - ``forwardDistance`` (float)
   * - ``CbNavigateBackwards``
     - Async
     - ``backwardDistance`` (float)
   * - ``CbNavigateNamedWaypoint``
     - Async
     - ``waypointName`` (string)
   * - ``CbNavigateNextWaypoint``
     - Async
     - optional ``NavigateNextWaypointOptions``
   * - ``CbUndoPathBackwards``
     - Async
     - (none) — retraces recorded odometry path
   * - ``CbAbortNavigation``
     - Sync
     - (none)

Rotation Behaviors
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Behavior
     - Type
     - Constructor Parameters
   * - ``CbRotate``
     - Async
     - ``rotateDegree`` (float), optional ``SpinningPlanner``
   * - ``CbAbsoluteRotate``
     - Async
     - ``targetYaw`` (float)
   * - ``CbPureSpinning``
     - Async
     - ``yawTarget`` (float), ``angularVelocity`` (float)
   * - ``CbRotateLookAt``
     - Async
     - ``targetPose`` (PoseStamped)
   * - ``CbSpiralMotion``
     - Async
     - spiral search parameters

Monitoring Behaviors
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Behavior
     - Type
     - Constructor Parameters
   * - ``CbWaitNav2Nodes``
     - Async
     - optional ``std::vector<Nav2Nodes>`` (default: PlannerServer, ControllerServer, BtNavigator)
   * - ``CbWaitPose``
     - Async
     - (none)
   * - ``CbWaitTransform``
     - Async
     - ``sourceFrame``, ``targetFrame``

SLAM Behaviors
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Behavior
     - Type
     - Constructor Parameters
   * - ``CbPauseSlam``
     - Service Call
     - optional ``serviceName`` (default ``"/slam_toolbox/pause_new_measurements"``)
   * - ``CbResumeSlam``
     - Service Call
     - optional ``serviceName``
   * - ``CbSaveSlamMap``
     - Sync
     - ``mapPath`` (string)

Events
------

Action events from ``ClNav2Z``:

- ``EvActionSucceeded<ClNav2Z, OrNavigation>`` — navigation goal reached
- ``EvActionAborted<ClNav2Z, OrNavigation>`` — navigation goal aborted
- ``EvActionCancelled<ClNav2Z, OrNavigation>`` — navigation goal cancelled
- ``EvActionFeedback<ClNav2Z, OrNavigation>`` — feedback received

Standard behavior events:

- ``EvCbSuccess<CbBehavior, OrNavigation>``
- ``EvCbFailure<CbBehavior, OrNavigation>``

Orthogonal Setup
-----------------

From ``sm_nav2_gazebo_test_1``:

.. code-block:: c++

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

Example Mission Flow
---------------------

From ``sm_nav2_gazebo_test_1`` — a navigation mission with localization, waypoints, and rotation:

.. code-block:: text

   StAllSensorsGo ──[Nav2 ready / 15s timer]──→ StSetInitialPose
     └── StSetInitialPose ──[success]──→ StNavigateToWaypoint1(2.0, 0.0)
           └── StNavigateToWaypoint1 ──[success]──→ StRotate(π rad)
                 └── StRotate ──[success]──→ StNavigateToWaypoint2(0.0, 0.0)
                       └── StNavigateToWaypoint2 ──[success]──→ StFinalState

Example state:

.. code-block:: c++

   struct StNavigateToWaypoint1
     : smacc2::SmaccState<StNavigateToWaypoint1, SmNav2GazeboTest1>
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
       // Navigate to (x=2.0, y=0.0, yaw=0.0) in the map frame
       configure_orthogonal<OrNavigation, CbNavigateGlobalPosition>(
           2.0, 0.0, 0.0);
       configure_orthogonal<OrKeyboard, CbDefaultKeyboardBehavior>();
     }
   };

Build and Run
--------------

.. code-block:: bash

   source /opt/ros/jazzy/setup.bash
   cd ~/ros2_ws
   colcon build --packages-select cl_nav2z sm_nav2_gazebo_test_1
   source install/setup.bash

   # Terminal 1: Nav2 + Gazebo simulation
   export TURTLEBOT3_MODEL=waffle
   ros2 launch nav2_bringup tb3_simulation_launch.py headless:=False

   # Terminal 2: State Machine
   ros2 launch sm_nav2_gazebo_test_1 sm_nav2_gazebo_test_1.py

Planner Presets
----------------

``CpPlannerSwitcher`` provides preset methods for common navigation patterns:

.. list-table::
   :header-rows: 1

   * - Method
     - Planner
     - Use Case
   * - ``setForwardPlanner()``
     - Default planner + controller
     - Standard forward navigation
   * - ``setBackwardPlanner()``
     - Backward-specific planner
     - Reverse navigation
   * - ``setPureSpinningPlanner()``
     - Spinning planner
     - In-place rotation
   * - ``setUndoPathBackwardPlanner()``
     - Backward path-following planner
     - Retracing recorded odometry paths
   * - ``setDefaultPlanners()``
     - Reset to defaults
     - Restore original planner configuration
