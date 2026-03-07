.. title:: How to Use MoveIt2 with SMACC2
.. meta::
   :description: Reference guide for using the ClMoveit2z client library with SMACC2 for robotic manipulation — components, behaviors, prerequisites, and example missions.

How to Use MoveIt2 with SMACC2
===============================

The ``cl_moveit2z`` client library integrates MoveIt2 with SMACC2 for robotic manipulation. This guide covers the client, its components, behaviors, and a complete example mission.

Getting Started
----------------

1. **MoveIt2** installed:

.. code-block:: bash

   sudo apt install ros-jazzy-moveit

2. **Robot description + MoveIt config** package (e.g., Panda):

.. code-block:: bash

   sudo apt install ros-jazzy-moveit-resources-panda-moveit-config

3. **MoveIt2 demo** running (provides move_group + RViz):

.. code-block:: bash

   ros2 launch moveit_resources_panda_moveit_config demo.launch.py

4. **cl_moveit2z** and ``sm_panda_cl_moveit2z_cb_inventory`` built in your colcon workspace

Overview
--------

``ClMoveit2z`` wraps the MoveIt2 ``MoveGroupInterface`` and ``PlanningSceneInterface``. It accepts a planning group name and creates the MoveIt interfaces on initialization:

.. code-block:: c++

   // ClMoveit2z constructors
   ClMoveit2z(std::string groupName);
   ClMoveit2z(const moveit::planning_interface::MoveGroupInterface::Options & options);

Unlike ``ClPx4Mr`` or ``ClNav2Z``, ``ClMoveit2z`` does not create components in ``onComponentInitialization()``. Instead, all components are created at the orthogonal level — see `Orthogonal Setup`_ below. This gives the state machine full control over which components are active.

Reference state machine: ``sm_panda_cl_moveit2z_cb_inventory``

Components
----------

.. list-table::
   :header-rows: 1

   * - Component
     - Purpose
     - Key Methods/Signals
   * - ``CpMotionPlanner``
     - Joint-space and Cartesian planning
     - ``planToPose()``, ``planToJointTarget()``, ``planCartesianPath()``
   * - ``CpTrajectoryExecutor``
     - Execute planned trajectories
     - ``execute()``, ``executePlan()``, ``cancel()``
   * - ``CpTrajectoryHistory``
     - Store executed trajectories for undo
     - ``getLastTrajectory()``, ``pushTrajectory()``
   * - ``CpTrajectoryVisualizer``
     - RViz trajectory visualization
     - ``setTrajectory()``, ``clearMarkers()``, ``setColor()``
   * - ``CpJointSpaceTrajectoryPlanner``
     - IK-based planning from Cartesian waypoints
     - ``planFromWaypoints()``
   * - ``CpTfListener``
     - Transform listener
     - ``lookupTransform()``, ``transformPose()``, ``canTransform()``
   * - ``CpGraspingComponent``
     - Collision objects for pick-and-place
     - ``createGraspableBox()``, ``getGraspingObject()``

Behaviors
---------

.. list-table::
   :header-rows: 1

   * - Behavior
     - Type
     - Constructor Parameters
   * - ``CbMoveJoints``
     - Async
     - ``jointValueTarget`` (map<string, double>), optional ``scalingFactor_``
   * - ``CbMoveEndEffector``
     - Async
     - ``targetPose`` (PoseStamped), optional ``tipLink``
   * - ``CbMoveKnownState``
     - Async
     - ``pkg`` (string), ``configPath`` (string) — loads joint values from YAML
   * - ``CbMoveCartesianRelative2``
     - Async
     - ``referenceFrame``, ``tipLink``, optional ``offset`` (Vector3)
   * - ``CbMoveEndEffectorTrajectory``
     - Async
     - ``endEffectorTrajectory`` (vector of PoseStamped), optional ``tipLink``
   * - ``CbEndEffectorRotate``
     - Async
     - ``deltaRadians`` (double), optional ``tipLink``
   * - ``CbCircularPivotMotion``
     - Async
     - ``planePivotPose`` (PoseStamped), ``deltaRadians``, optional ``tipLink``
   * - ``CbAttachObject``
     - Async
     - optional ``targetObjectName`` (string)
   * - ``CbDetachObject``
     - Async
     - (none)
   * - ``CbUndoLastTrajectory``
     - Async
     - optional ``backIndex`` (int, default -1 = most recent)

All behaviors post ``EvCbSuccess`` on completion and ``EvCbFailure`` on error.

Events
------

- ``EvMoveGroupMotionExecutionSucceded<TSource, TOrthogonal>`` — motion completed successfully
- ``EvMoveGroupMotionExecutionFailed<TSource, TOrthogonal>`` — motion failed

Standard async behavior events also apply:

- ``EvCbSuccess<CbBehavior, OrManipulation>``
- ``EvCbFailure<CbBehavior, OrManipulation>``

Trajectory behaviors may also post:

- ``EvJointDiscontinuity<CbBehavior, OrManipulation>`` — IK produced a joint space discontinuity
- ``EvIncorrectInitialPosition<CbBehavior, OrManipulation>`` — current position doesn't match trajectory start

Orthogonal Setup
-----------------

From ``sm_panda_cl_moveit2z_cb_inventory`` — creates the client and all components:

.. code-block:: c++

   class OrArm : public smacc2::Orthogonal<OrArm>
   {
   public:
     void onInitialize() override
     {
       auto move_group_client =
         this->createClient<cl_moveit2z::ClMoveit2z>("panda_arm");

       // Core components for component-based architecture
       move_group_client->createComponent<
         cl_moveit2z::CpJointSpaceTrajectoryPlanner>();
       move_group_client->createComponent<
         cl_moveit2z::CpTrajectoryExecutor>();
       move_group_client->createComponent<
         cl_moveit2z::CpTfListener>();
       move_group_client->createComponent<
         cl_moveit2z::CpTrajectoryVisualizer>();
       move_group_client->createComponent<
         cl_moveit2z::CpTrajectoryHistory>();

       auto graspingComponent = move_group_client->createComponent<
         cl_moveit2z::CpGraspingComponent>();
       graspingComponent->gripperLink_ = "tool0";
       graspingComponent->createGraspableBox(
         "virtualBox", 0, 0.5, 0.5, 0.1, 0.1, 0.1);
     }
   };

Example Mission Flow
---------------------

From ``sm_panda_cl_moveit2z_cb_inventory`` — a manipulation behavior inventory:

.. code-block:: text

   StPause1 ──[15s timer]──→ StAcquireSensors ──[joint_states msg]──→
     StMoveKnownState1 ──[success]──→ StPause2 ──→
       StMoveJoints1 ──[success]──→ StPause3 ──→
         StMoveJoints2 ──[success]──→ StPause4 ──→
           StMoveKnownState2 ──[success]──→ StPause5 ──→
             StMoveCartesianRelative2 ──[success]──→ StPause6 ──→
               StUndoLastTrajectory ──[success]──→ StPause7 ──→
                 StMoveJoints3 ──[success]──→ StPause8 ──→
                   StEndEffectorRotate ──[success]──→ StPause9 ──→
                     StMoveJoints4 ──[success]──→ StPause10 ──→
                       StMoveEndEffector ──[success]──→ ...

Example state:

.. code-block:: c++

   struct StMoveEndEffector
     : smacc2::SmaccState<StMoveEndEffector, SmPandaClMoveit2zCbInventory>
   {
     using SmaccState::SmaccState;

     typedef boost::mpl::list<
       Transition<EvCbSuccess<CbMoveEndEffector, OrArm>,
                  StPause11, SUCCESS>
     > reactions;

     static void staticConfigure()
     {
       geometry_msgs::msg::PoseStamped target_pose;
       target_pose.header.frame_id = "panda_link0";
       target_pose.pose.position.x = 0.3;
       target_pose.pose.position.y = 0.2;
       target_pose.pose.position.z = 0.4;
       target_pose.pose.orientation.z = 0.383;  // sin(45°/2)
       target_pose.pose.orientation.w = 0.924;  // cos(45°/2)

       configure_orthogonal<OrArm, CbMoveEndEffector>(
           target_pose, "panda_link8");
       configure_orthogonal<OrKeyboard, CbDefaultKeyboardBehavior>();
     }
   };

Build and Run
--------------

.. code-block:: bash

   source /opt/ros/jazzy/setup.bash
   cd ~/ros2_ws
   colcon build --packages-select cl_moveit2z sm_panda_cl_moveit2z_cb_inventory
   source install/setup.bash

   # Terminal 1: MoveIt2 Demo (move_group + RViz)
   ros2 launch moveit_resources_panda_moveit_config demo.launch.py

   # Terminal 2: State Machine
   ros2 launch sm_panda_cl_moveit2z_cb_inventory \
     sm_panda_cl_moveit2z_cb_inventory.py

SOFT Requirement Pattern
-------------------------

MoveIt2 behaviors use the ``SOFT`` requirement pattern for optional component access. When a behavior calls ``requiresComponent()`` with ``ComponentRequirement::SOFT``, it gracefully degrades if the component isn't present:

.. code-block:: c++

   // Inside a behavior's onEntry():
   CpMotionPlanner * motionPlanner = nullptr;
   this->requiresComponent(motionPlanner,
     smacc2::ComponentRequirement::SOFT);

   if (motionPlanner != nullptr)
   {
     // Use component-based approach (preferred)
     auto result = motionPlanner->planToJointTarget(
         jointValueTarget_, options);
   }
   else
   {
     // Fallback to legacy direct MoveGroupInterface calls
     moveGroupInterface.setJointValueTarget(jointValueTarget_);
     auto result = moveGroupInterface.plan(plan);
   }

This pattern appears throughout MoveIt2 behaviors:

- ``CpTrajectoryHistory`` — if available, trajectories are recorded for undo; otherwise, ``CbUndoLastTrajectory`` won't work but other behaviors function normally
- ``CpTrajectoryVisualizer`` — if available, trajectories are visualized in RViz; otherwise, fallback markers are used
- ``CpMotionPlanner`` — if available, used for planning; otherwise, direct ``MoveGroupInterface`` calls

The contrast with ``HARD`` (the default): a ``HARD`` requirement causes an error if the component is missing. Use ``HARD`` for components that are essential to your behavior, and ``SOFT`` for optional enhancements.

Planning Groups and Frames
---------------------------

MoveIt2 organizes joints into **planning groups** defined in the robot's SRDF. The group name passed to ``ClMoveit2z`` determines which joints the planner controls:

.. list-table::
   :header-rows: 1

   * - Parameter
     - Example (Panda)
     - Description
   * - Planning group
     - ``"panda_arm"``
     - Joint group for motion planning
   * - End-effector link
     - ``"panda_link8"``
     - Tip link for Cartesian goals
   * - Reference frame
     - ``"panda_link0"``
     - Base frame for pose targets
   * - Gripper link
     - ``"tool0"``
     - Link for object attachment

Pose targets use ``geometry_msgs::msg::PoseStamped`` with a ``frame_id`` matching the robot's reference frame. Orientation is specified as a quaternion.
