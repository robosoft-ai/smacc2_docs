.. title:: How to Use Nav2 with SMACC2
.. meta::
   :description: Reference guide for using the ClNav2Z client library with SMACC2 — components, behaviors, events, and navigation patterns.

How to Use Nav2 with SMACC2
============================

The ``cl_nav2z`` client library integrates Nav2 with SMACC2 for autonomous navigation. This guide covers the client, its components, behaviors, and common patterns.

Overview
--------

``ClNav2Z`` is a component-based client that wraps Nav2's ``NavigateToPose`` action. It provides waypoint navigation, path tracking, planner switching, and localization support.

.. code-block:: c++

   #include <cl_nav2z/cl_nav2z.hpp>

Reference state machine: ``sm_nav2_gazebo_test_1``

Orthogonal Setup
-----------------

.. code-block:: c++

   class OrNavigation : public smacc2::Orthogonal<OrNavigation>
   {
   public:
     void onInitialize() override
     {
       auto client = this->createClient<cl_nav2z::ClNav2Z>();
       client->createComponent<cl_nav2z::CpPose>("/base_link", "/map");
       client->createComponent<cl_nav2z::CpOdomTracker>();
       client->createComponent<cl_nav2z::CpPlannerSwitcher>();
       client->createComponent<cl_nav2z::CpGoalCheckerSwitcher>();
       client->createComponent<cl_nav2z::CpAmcl>();
     }
   };

Components
----------

.. list-table::
   :header-rows: 1

   * - Component
     - Purpose
   * - ``CpPose``
     - Robot pose from TF (configurable source and target frames)
   * - ``CpOdomTracker``
     - Records odometry path for undo/backtrack operations
   * - ``CpPlannerSwitcher``
     - Switches between planners and controllers at runtime
   * - ``CpGoalCheckerSwitcher``
     - Switches goal checker algorithms
   * - ``CpAmcl``
     - Sets initial pose for AMCL localization
   * - ``CpWaypointsNavigator``
     - Multi-waypoint navigation with sequential execution
   * - ``CpWaypointsVisualizer``
     - Publishes waypoint markers for RViz
   * - ``CpWaypointsEventDispatcher``
     - Dispatches waypoint-specific events
   * - ``CpSlamToolbox``
     - SLAM Toolbox integration (pause, resume, save map)
   * - ``CpCostmapSwitch``
     - Enable/disable costmap layers at runtime
   * - ``CpNav2ActionInterface``
     - Low-level Nav2 action client wrapper

Navigation Behaviors
---------------------

.. list-table::
   :header-rows: 1

   * - Behavior
     - Purpose
   * - ``CbNavigateGlobalPosition``
     - Navigate to an (x, y, yaw) position in the map frame
   * - ``CbNavigateForward``
     - Navigate forward a specified distance
   * - ``CbNavigateBackwards``
     - Navigate backwards using the backward planner
   * - ``CbNavigateNamedWaypoint``
     - Navigate to a waypoint loaded from a YAML file
   * - ``CbNavigateNextWaypoint``
     - Navigate to the next waypoint in a loaded sequence
   * - ``CbUndoPathBackwards``
     - Retrace the recorded odometry path in reverse
   * - ``CbAbortNavigation``
     - Cancel the active navigation goal

Rotation Behaviors
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Behavior
     - Purpose
   * - ``CbRotate``
     - Rotate by a relative angle
   * - ``CbAbsoluteRotate``
     - Rotate to an absolute heading
   * - ``CbPureSpinning``
     - Continuous spinning using a custom local planner
   * - ``CbRotateLookAt``
     - Rotate to face a target position
   * - ``CbSpiralMotion``
     - Spiral search pattern

Monitoring Behaviors
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Behavior
     - Purpose
   * - ``CbWaitNav2Nodes``
     - Wait for Nav2 lifecycle nodes to become active
   * - ``CbWaitPose``
     - Wait for the robot pose to become available
   * - ``CbWaitTransform``
     - Wait for a TF transform to become available

SLAM Behaviors
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Behavior
     - Purpose
   * - ``CbPauseSlam``
     - Pause SLAM Toolbox updates
   * - ``CbResumeSlam``
     - Resume SLAM Toolbox updates
   * - ``CbSaveSlamMap``
     - Save the current SLAM map

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

Example: Navigate to Two Waypoints
------------------------------------

.. code-block:: c++

   struct StNavigate1 : smacc2::SmaccState<StNavigate1, SmExample>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvActionSucceeded<ClNav2Z, OrNavigation>,
                  StNavigate2, SUCCESS>,
       Transition<EvActionAborted<ClNav2Z, OrNavigation>,
                  StError, ABORT>
       >reactions;

     static void staticConfigure()
     {
       configure_orthogonal<OrNavigation, CbNavigateGlobalPosition>(
           2.0, 0.0, 0.0);  // x, y, yaw
     }
   };

   struct StNavigate2 : smacc2::SmaccState<StNavigate2, SmExample>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvActionSucceeded<ClNav2Z, OrNavigation>,
                  StDone, SUCCESS>
       >reactions;

     static void staticConfigure()
     {
       configure_orthogonal<OrNavigation, CbNavigateGlobalPosition>(
           0.0, 0.0, 0.0);  // return to origin
     }
   };
