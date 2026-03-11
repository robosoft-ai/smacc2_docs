.. title:: How to Use MoveIt2 with SMACC2
.. meta::
   :description: Complete guide for using the ClMoveit2z client library with SMACC2 for robotic manipulation — getting started, library tour, and usage patterns including writing custom behaviors and components.

How to Use MoveIt2 with SMACC2
===============================

Getting Started
----------------

Required Installations
~~~~~~~~~~~~~~~~~~~~~~~

**ROS 2 Jazzy**

.. code-block:: bash

   # Follow https://docs.ros.org/en/jazzy/Installation.html
   sudo apt install ros-jazzy-desktop

**MoveIt2**

.. code-block:: bash

   sudo apt install ros-jazzy-moveit

**Robot Description + MoveIt Config** (e.g., Panda):

.. code-block:: bash

   sudo apt install ros-jazzy-moveit-resources-panda-moveit-config

Assembling the Workspace
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src

   # SMACC2 framework and client libraries
   git clone https://github.com/robosoft-ai/SMACC2.git -b jazzy

The packages you need are:

- ``smacc2`` — core state machine framework
- ``smacc2_msgs`` — SMACC2 message definitions
- ``cl_moveit2z`` — MoveIt2 client library (inside ``SMACC2/smacc2_client_library/``)
- ``sm_panda_cl_moveit2z_cb_inventory`` — reference state machine (inside ``SMACC2/smacc2_sm_reference_library/``)

Building the Workspace
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd ~/ros2_ws
   source /opt/ros/jazzy/setup.bash
   colcon build --packages-select cl_moveit2z sm_panda_cl_moveit2z_cb_inventory
   source install/setup.bash

.. note::

   You can also use ``colcon build --packages-up-to sm_panda_cl_moveit2z_cb_inventory``
   to build only the required dependency chain.

Launching the Application
~~~~~~~~~~~~~~~~~~~~~~~~~~

You need **two terminals**. Source the workspace in each:

.. code-block:: bash

   source ~/ros2_ws/install/setup.bash

**Terminal 1 — MoveIt2 Demo (move_group + RViz)**

.. code-block:: bash

   ros2 launch moveit_resources_panda_moveit_config demo.launch.py

**Terminal 2 — State Machine**

.. code-block:: bash

   source ~/ros2_ws/install/setup.bash
   ros2 launch sm_panda_cl_moveit2z_cb_inventory \
     sm_panda_cl_moveit2z_cb_inventory.py

The state machine executes a behavior inventory automatically:

.. code-block:: text

   Wait(15s) → AcquireSensors → MoveKnownState → MoveJoints → MoveCartesianRelative →
     UndoLastTrajectory → EndEffectorRotate → MoveEndEffector → ...

Monitor with:

.. code-block:: bash

   # Current state
   ros2 topic echo /sm_panda_cl_moveit2z_cb_inventory/smacc/status

   # Transition log
   ros2 topic echo /sm_panda_cl_moveit2z_cb_inventory/smacc/transition_log

Tour of the MoveIt2 Client Behavior Library
---------------------------------------------

The ``cl_moveit2z`` client library wraps the MoveIt2 ``MoveGroupInterface``
and ``PlanningSceneInterface`` for SMACC2 integration. It provides
component-based motion planning, trajectory execution, and object
manipulation.

For the full API reference, see the
`cl_moveit2z source <https://github.com/robosoft-ai/SMACC2/tree/jazzy/smacc2_client_library/cl_moveit2z>`_.

Folder Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

   cl_moveit2z/
   ├── include/cl_moveit2z/
   │   ├── cl_moveit2z.hpp                        # Client
   │   ├── client_behaviors.hpp                    # Behavior includes
   │   ├── common.hpp
   │   ├── client_behaviors/
   │   │   ├── cb_move_joints.hpp
   │   │   ├── cb_move_end_effector.hpp
   │   │   ├── cb_move_known_state.hpp
   │   │   ├── cb_move_cartesian_relative2.hpp
   │   │   ├── cb_move_end_effector_trajectory.hpp
   │   │   ├── cb_end_effector_rotate.hpp
   │   │   ├── cb_circular_pivot_motion.hpp
   │   │   ├── cb_attach_object.hpp
   │   │   ├── cb_detach_object.hpp
   │   │   └── cb_undo_last_trajectory.hpp
   │   └── components/
   │       ├── cp_motion_planner.hpp
   │       ├── cp_trajectory_executor.hpp
   │       ├── cp_trajectory_history.hpp
   │       ├── cp_trajectory_visualizer.hpp
   │       ├── cp_joint_space_trajectory_planner.hpp
   │       ├── cp_tf_listener.hpp
   │       └── cp_grasping_objects.hpp
   ├── src/cl_moveit2z/
   │   └── cl_moveit2z.cpp
   ├── CMakeLists.txt
   └── package.xml

Components
~~~~~~~~~~~

Unlike ``ClPx4Mr`` or ``ClNav2Z``, ``ClMoveit2z`` does not create components
in ``onComponentInitialization()``. All components are created at the
orthogonal level, giving the state machine full control over which components
are active.

.. code-block:: c++

   // ClMoveit2z constructors
   ClMoveit2z(std::string groupName);
   ClMoveit2z(const moveit::planning_interface::MoveGroupInterface::Options & options);

.. list-table::
   :header-rows: 1

   * - Component
     - Purpose
     - Key Methods / Signals
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
~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Behavior
     - Constructor Parameters
     - Description
   * - ``CbMoveJoints``
     - ``jointValueTarget`` (map<string, double>), optional ``scalingFactor_``
     - Move to a joint configuration
   * - ``CbMoveEndEffector``
     - ``targetPose`` (PoseStamped), optional ``tipLink``
     - Move end-effector to a Cartesian pose
   * - ``CbMoveKnownState``
     - ``pkg`` (string), ``configPath`` (string)
     - Load joint values from YAML and move
   * - ``CbMoveCartesianRelative2``
     - ``referenceFrame``, ``tipLink``, optional ``offset`` (Vector3)
     - Relative Cartesian motion
   * - ``CbMoveEndEffectorTrajectory``
     - ``endEffectorTrajectory`` (vector of PoseStamped), optional ``tipLink``
     - Follow a Cartesian trajectory
   * - ``CbEndEffectorRotate``
     - ``deltaRadians`` (double), optional ``tipLink``
     - Rotate end-effector around its Z-axis
   * - ``CbCircularPivotMotion``
     - ``planePivotPose`` (PoseStamped), ``deltaRadians``, optional ``tipLink``
     - Circular pivot motion
   * - ``CbAttachObject``
     - optional ``targetObjectName`` (string)
     - Attach a collision object to the gripper
   * - ``CbDetachObject``
     - (none)
     - Detach the attached collision object
   * - ``CbUndoLastTrajectory``
     - optional ``backIndex`` (int, default -1)
     - Replay a recorded trajectory in reverse

All behaviors post ``EvCbSuccess`` on completion and ``EvCbFailure`` on error.
Trajectory behaviors may also post ``EvJointDiscontinuity`` or
``EvIncorrectInitialPosition``.

Using the MoveIt2 Client Behavior Library
-------------------------------------------

Configuring the Orthogonal
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create an orthogonal that instantiates the ``ClMoveit2z`` client with a
planning group name, then add the components you need:

.. code-block:: c++

   #include <cl_moveit2z/cl_moveit2z.hpp>

   class OrArm : public smacc2::Orthogonal<OrArm>
   {
   public:
     void onInitialize() override
     {
       auto client =
         this->createClient<cl_moveit2z::ClMoveit2z>("panda_arm");

       client->createComponent<cl_moveit2z::CpJointSpaceTrajectoryPlanner>();
       client->createComponent<cl_moveit2z::CpTrajectoryExecutor>();
       client->createComponent<cl_moveit2z::CpTfListener>();
       client->createComponent<cl_moveit2z::CpTrajectoryVisualizer>();
       client->createComponent<cl_moveit2z::CpTrajectoryHistory>();

       auto graspingComponent = client->createComponent<
         cl_moveit2z::CpGraspingComponent>();
       graspingComponent->gripperLink_ = "tool0";
       graspingComponent->createGraspableBox(
         "virtualBox", 0, 0.5, 0.5, 0.1, 0.1, 0.1);
     }
   };

Register the orthogonal in your state machine's ``onInitialize()``:

.. code-block:: c++

   struct SmMyManipulation
     : smacc2::SmaccStateMachineBase<SmMyManipulation, StInitial>
   {
     void onInitialize() override
     {
       this->createOrthogonal<OrArm>();
     }
   };

Using a Behavior
~~~~~~~~~~~~~~~~~

Behaviors are configured in a state's ``staticConfigure()`` using
``configure_orthogonal<>``. Constructor parameters are passed as arguments.
The behavior executes asynchronously on state entry and posts events
that drive transitions:

.. code-block:: c++

   #include <cl_moveit2z/client_behaviors/cb_move_joints.hpp>

   struct StMoveJoints1
     : smacc2::SmaccState<StMoveJoints1, SmMyManipulation>
   {
     using SmaccState::SmaccState;

     typedef boost::mpl::list<
       Transition<EvCbSuccess<CbMoveJoints, OrArm>, StNextState, SUCCESS>
     > reactions;

     static void staticConfigure()
     {
       std::map<std::string, double> jointValues{
         {"panda_joint1", 0.0},
         {"panda_joint2", 0.0},
         {"panda_joint3", 0.0},
         {"panda_joint4", -M_PI / 2},
         {"panda_joint5", 0.0},
         {"panda_joint6", M_PI / 2},
         {"panda_joint7", 0.0}
       };
       configure_orthogonal<OrArm, CbMoveJoints>(jointValues);
     }

     void runtimeConfigure()
     {
       // Optional: adjust behavior parameters after instantiation
       this->getClientBehavior<OrArm, CbMoveJoints>()->scalingFactor_ = 1;
     }
   };

The pattern is the same for all MoveIt2 behaviors — change the behavior
class and its parameters:

.. code-block:: c++

   // Move end-effector to a Cartesian pose
   geometry_msgs::msg::PoseStamped target_pose;
   target_pose.header.frame_id = "panda_link0";
   target_pose.pose.position.x = 0.3;
   target_pose.pose.position.y = 0.2;
   target_pose.pose.position.z = 0.4;
   target_pose.pose.orientation.w = 1.0;
   configure_orthogonal<OrArm, CbMoveEndEffector>(target_pose, "panda_link8");

   // Move to a named configuration loaded from YAML
   configure_orthogonal<OrArm, CbMoveKnownState>(
       "sm_panda_cl_moveit2z_cb_inventory", "config/known_states/home.yaml");

   // Rotate end-effector 90 degrees around its Z-axis
   configure_orthogonal<OrArm, CbEndEffectorRotate>(M_PI / 2);

SOFT Requirement Pattern
^^^^^^^^^^^^^^^^^^^^^^^^^

MoveIt2 behaviors use the ``SOFT`` requirement pattern for optional
component access. When a behavior calls ``requiresComponent()`` with
``ComponentRequirement::SOFT``, it gracefully degrades if the component
isn't present:

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

The contrast with ``HARD`` (the default): a ``HARD`` requirement causes an
error if the component is missing. Use ``HARD`` for essential components,
``SOFT`` for optional enhancements.

Planning Groups and Frames
^^^^^^^^^^^^^^^^^^^^^^^^^^^

MoveIt2 organizes joints into **planning groups** defined in the robot's
SRDF. The group name passed to ``ClMoveit2z`` determines which joints the
planner controls:

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

Writing Your Own Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~

To add a new manipulation behavior, create a class that inherits from
``SmaccAsyncClientBehavior``, acquires the components it needs, and posts
events when done.

Here is a complete example — a behavior that moves to a joint configuration
and then opens the gripper:

**Header** (``include/cl_moveit2z/client_behaviors/cb_move_and_open_gripper.hpp``):

.. code-block:: c++

   #pragma once

   #include <smacc2/smacc.hpp>

   namespace cl_moveit2z
   {

   class CpMotionPlanner;
   class CpTrajectoryExecutor;

   class CbMoveAndOpenGripper : public smacc2::SmaccAsyncClientBehavior
   {
   public:
     CbMoveAndOpenGripper(
       std::map<std::string, double> jointTarget);

     void onEntry() override;
     void onExit() override;

   private:
     std::map<std::string, double> jointTarget_;
     CpMotionPlanner * motionPlanner_ = nullptr;
     CpTrajectoryExecutor * executor_ = nullptr;
   };

   }  // namespace cl_moveit2z

**Source** (``src/cl_moveit2z/client_behaviors/cb_move_and_open_gripper.cpp``):

.. code-block:: c++

   #include <cl_moveit2z/client_behaviors/cb_move_and_open_gripper.hpp>
   #include <cl_moveit2z/components/cp_motion_planner.hpp>
   #include <cl_moveit2z/components/cp_trajectory_executor.hpp>

   namespace cl_moveit2z
   {

   CbMoveAndOpenGripper::CbMoveAndOpenGripper(
     std::map<std::string, double> jointTarget)
   : jointTarget_(jointTarget)
   {
   }

   void CbMoveAndOpenGripper::onEntry()
   {
     // 1. Acquire components
     this->requiresComponent(motionPlanner_);
     this->requiresComponent(executor_);

     // 2. Plan to joint target
     moveit::planning_interface::MoveGroupInterface::Plan plan;
     auto result = motionPlanner_->planToJointTarget(jointTarget_);

     if (result)
     {
       // 3. Execute the plan
       executor_->executePlan(result.value());
       this->postSuccessEvent();
     }
     else
     {
       RCLCPP_ERROR(getLogger(), "Planning failed");
       this->postFailureEvent();
     }
   }

   void CbMoveAndOpenGripper::onExit() {}

   }  // namespace cl_moveit2z

The key steps for any custom MoveIt2 behavior:

1. **Acquire components** with ``requiresComponent()`` in ``onEntry()``
2. **Plan** through ``CpMotionPlanner``
3. **Execute** through ``CpTrajectoryExecutor``
4. **Post events** (``postSuccessEvent()`` / ``postFailureEvent()``)
5. **Clean up** in ``onExit()``

Writing Your Own Component
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Components manage reusable logic that multiple behaviors share. Write a new
component when you need to:

- Add planning scene management not covered by existing components
- Implement custom motion planning strategies
- Add reusable monitoring (e.g., force/torque thresholds)

A component inherits from ``ISmaccComponent`` and optionally from
``ISmaccUpdatable`` for periodic updates.

Here is a complete example — a component that manages named joint
configurations:

**Header** (``include/cl_moveit2z/components/cp_named_configurations.hpp``):

.. code-block:: c++

   #pragma once

   #include <smacc2/smacc.hpp>
   #include <map>
   #include <string>

   namespace cl_moveit2z
   {

   class CpNamedConfigurations : public smacc2::ISmaccComponent
   {
   public:
     CpNamedConfigurations();
     virtual ~CpNamedConfigurations();

     void onInitialize() override;

     void addConfiguration(const std::string & name,
       const std::map<std::string, double> & joints);
     std::map<std::string, double> getConfiguration(
       const std::string & name) const;
     bool hasConfiguration(const std::string & name) const;

   private:
     std::map<std::string, std::map<std::string, double>> configs_;
   };

   }  // namespace cl_moveit2z

**Source** (``src/cl_moveit2z/components/cp_named_configurations.cpp``):

.. code-block:: c++

   #include <cl_moveit2z/components/cp_named_configurations.hpp>

   namespace cl_moveit2z
   {

   CpNamedConfigurations::CpNamedConfigurations() {}
   CpNamedConfigurations::~CpNamedConfigurations() {}

   void CpNamedConfigurations::onInitialize()
   {
     RCLCPP_INFO(getLogger(), "CpNamedConfigurations: initialized");
   }

   void CpNamedConfigurations::addConfiguration(
     const std::string & name,
     const std::map<std::string, double> & joints)
   {
     configs_[name] = joints;
   }

   std::map<std::string, double>
   CpNamedConfigurations::getConfiguration(
     const std::string & name) const
   {
     return configs_.at(name);
   }

   bool CpNamedConfigurations::hasConfiguration(
     const std::string & name) const
   {
     return configs_.count(name) > 0;
   }

   }  // namespace cl_moveit2z

Add the component at the orthogonal level:

.. code-block:: c++

   auto configs = client->createComponent<cl_moveit2z::CpNamedConfigurations>();
   configs->addConfiguration("home", {
     {"panda_joint1", 0.0}, {"panda_joint2", 0.0},
     {"panda_joint3", 0.0}, {"panda_joint4", -M_PI/2},
     {"panda_joint5", 0.0}, {"panda_joint6", M_PI/2},
     {"panda_joint7", 0.0}
   });

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
