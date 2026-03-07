.. title:: How to Use MoveIt2 with SMACC2
.. meta::
   :description: Reference guide for using the ClMoveit2z client library with SMACC2 — components, behaviors, events, and the SOFT requirement pattern.

How to Use MoveIt2 with SMACC2
===============================

The ``cl_moveit2z`` client library integrates MoveIt2 with SMACC2 for robotic manipulation. This guide covers the client, its components, behaviors, and events.

Overview
--------

``ClMoveit2z`` wraps the MoveIt2 ``MoveGroupInterface`` and ``PlanningSceneInterface``. It provides component-based trajectory planning and execution.

.. code-block:: c++

   #include <cl_moveit2z/cl_moveit2z.hpp>

Reference state machine: ``sm_panda_cl_moveit2z_cb_inventory``

|

Orthogonal Setup
-----------------

.. code-block:: c++

   class OrManipulation : public smacc2::Orthogonal<OrManipulation>
   {
   public:
     void onInitialize() override
     {
       auto client = this->createClient<cl_moveit2z::ClMoveit2z>("panda_arm");
     }
   };

The constructor argument is the MoveIt2 planning group name (e.g., ``"panda_arm"``).

|

Components
----------

.. list-table::
   :header-rows: 1

   * - Component
     - Purpose
   * - ``CpMotionPlanner``
     - Joint-space and Cartesian motion planning
   * - ``CpTrajectoryExecutor``
     - Executes planned trajectories
   * - ``CpTrajectoryHistory``
     - Stores executed trajectories for undo operations
   * - ``CpTrajectoryVisualizer``
     - Publishes planned trajectories for RViz visualization
   * - ``CpJointSpaceTrajectoryPlanner``
     - Plans in joint space (alternative to Cartesian)
   * - ``CpTfListener``
     - Transform listener for coordinate conversions
   * - ``CpGraspingObjects``
     - Manages collision objects for pick-and-place

|

Behaviors
---------

.. list-table::
   :header-rows: 1

   * - Behavior
     - Type
     - Purpose
   * - ``CbMoveJoints``
     - Async
     - Move to a target joint configuration
   * - ``CbMoveEndEffector``
     - Async
     - Move end-effector to a target pose
   * - ``CbMoveKnownState``
     - Async
     - Move to a predefined named configuration
   * - ``CbMoveCartesianRelative2``
     - Async
     - Relative Cartesian motion (dx, dy, dz)
   * - ``CbMoveEndEffectorTrajectory``
     - Async
     - Follow a sequence of end-effector poses
   * - ``CbEndEffectorRotate``
     - Async
     - Rotate end-effector around an axis
   * - ``CbCircularPivotMotion``
     - Async
     - Circular motion around a pivot point
   * - ``CbAttachObject``
     - Sync
     - Attach a collision object to the end-effector
   * - ``CbDetachObject``
     - Sync
     - Detach a collision object
   * - ``CbUndoLastTrajectory``
     - Async
     - Reverse the last executed trajectory

|

Events
------

- ``EvMoveGroupMotionExecutionSucceded<TSource, TOrthogonal>`` — motion completed successfully
- ``EvMoveGroupMotionExecutionFailed<TSource, TOrthogonal>`` — motion failed

Standard async behavior events also apply:

- ``EvCbSuccess<CbBehavior, OrManipulation>``
- ``EvCbFailure<CbBehavior, OrManipulation>``

|

Example State
--------------

.. code-block:: c++

   struct StMoveToHome : smacc2::SmaccState<StMoveToHome, SmExample>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvCbSuccess<CbMoveKnownState, OrManipulation>,
                  StNextState, SUCCESS>,
       Transition<EvCbFailure<CbMoveKnownState, OrManipulation>,
                  StError, ABORT>
       >reactions;

     static void staticConfigure()
     {
       configure_orthogonal<OrManipulation, CbMoveKnownState>("home");
     }
   };

|

SOFT Requirement Pattern
-------------------------

MoveIt2 behaviors use the ``SOFT`` requirement pattern for optional component access — if a component is available it is used, otherwise the behavior proceeds without it. This allows the same behavior to work with different client configurations.
