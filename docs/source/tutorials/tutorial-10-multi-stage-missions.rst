.. title:: Tutorial 10 — Multi-Stage Missions
.. meta::
   :description: Build complex multi-stage autonomous missions with SMACC2 using mode states, super state sequences, and the PX4 flight mission as a real-world example.

Tutorial 10 — Multi-Stage Missions
===================================

This tutorial brings together everything you have learned to study two complete multi-stage state machines: ``sm_multi_stage_1`` (a complex hierarchical demo) and ``sm_cl_px4_mr_test_1`` (a real-world PX4 flight mission).

sm_multi_stage_1: Architecture
-------------------------------

``sm_multi_stage_1`` demonstrates the largest SMACC2 hierarchical pattern:

.. code-block:: text

   SmMultiStage1
   ├── MsMode1
   │   ├── SequenceA (loop: StiLoop → Sti1 → Sti2 → ... → Sti9)
   │   ├── SequenceB
   │   ├── SequenceC
   │   └── SequenceD → EvLoopEnd → MsMode2
   ├── MsMode2
   │   ├── SequenceA → SequenceB → SequenceC → SequenceD → MsMode3
   ├── MsMode3
   │   └── ... → MsMode4
   ├── MsMode4
   │   └── ... → MsMode5
   ├── MsMode5
   │   └── ... (terminal or loop back)
   ├── MsRecovery1
   │   └── Recovery sequences → MsMode::deep_history
   └── MsRecovery2
       └── Recovery sequences → MsMode::deep_history

Key patterns:

- **5 operational modes** with multiple sequences each
- **Recovery modes** that restore the previous state via deep history
- **Sequence super states** with inner loop states (each sequence loops through 9 steps)
- **Mode-to-mode transitions** via ``EvLoopEnd<SequenceD>``

Mode State Transitions
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c++

   struct MsMode1 : smacc2::SmaccState<MsMode1, SmMultiStage1, SequenceA>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvLoopEnd<SequenceD>, MsMode2>
       >reactions;
   };

When ``SequenceD`` inside ``MsMode1`` finishes its loop iterations, it posts ``EvLoopEnd<SequenceD>``. The mode state catches this and transitions to ``MsMode2``.

|

sm_cl_px4_mr_test_1: Real-World Mission
-----------------------------------------

This state machine flies a PX4 multirotor through a complete mission: arm → takeoff → navigate → orbit → return → land.

State Machine Definition
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c++

   // sm_cl_px4_mr_test_1.hpp
   struct SmClPx4MrTest1
     : public smacc2::SmaccStateMachineBase<SmClPx4MrTest1, MsDisarmedOnGround>
   {
     using SmaccStateMachineBase::SmaccStateMachineBase;

     virtual void onInitialize() override
     {
       this->createOrthogonal<OrPx4>();
       this->createOrthogonal<OrTimer>();
     }
   };

Mode States
~~~~~~~~~~~~

The mission is organized into 6 flight phases, each a mode state:

.. list-table::
   :header-rows: 1

   * - Mode State
     - Initial Child
     - Purpose
   * - ``MsDisarmedOnGround``
     - ``StWaitForReady``
     - Wait for PX4 topics
   * - ``MsArmedOnGround``
     - ``StArmPx4``
     - Arm the vehicle
   * - ``MsTakeoff``
     - ``StTakeoff``
     - Climb to target altitude
   * - ``MsInFlight``
     - ``StGoToWaypoint1``
     - Execute mission waypoints
   * - ``MsLanding``
     - ``StLand``
     - Descend and touch down
   * - ``MsLanded``
     - (terminal)
     - Mission complete

Mission Flow
~~~~~~~~~~~~~

.. code-block:: text

   MsDisarmedOnGround
     └── StWaitForReady ──[EvTimer]──→ MsArmedOnGround
           └── StArmPx4 ──[EvCbSuccess]──→ MsTakeoff
                 └── StTakeoff(5.0m) ──[EvCbSuccess]──→ MsInFlight
                       ├── StGoToWaypoint1(10,0,-5) ──[EvCbSuccess]──→
                       ├── StOrbitLocation(r=5,n=3) ──[EvCbSuccess]──→
                       └── StReturnToBase(0,0,-5) ──[EvCbSuccess]──→ MsLanding
                             └── StLand ──[EvCbSuccess]──→ MsLanded

Each state uses a single behavior that posts ``EvCbSuccess`` on completion:

.. code-block:: c++

   // states/in_flight/st_go_to_waypoint_1.hpp
   struct StGoToWaypoint1 : smacc2::SmaccState<StGoToWaypoint1, MsInFlight>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvCbSuccess<CbGoToLocation, OrPx4>, StOrbitLocation, SUCCESS>
       >reactions;

     static void staticConfigure()
     {
       // NED coordinates: 10m North, 0m East, 5m altitude (negative Z = up)
       configure_orthogonal<OrPx4, CbGoToLocation>(10.0f, 0.0f, -5.0f);
     }
   };

.. code-block:: c++

   // states/in_flight/st_orbit_location.hpp
   struct StOrbitLocation : smacc2::SmaccState<StOrbitLocation, MsInFlight>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvCbSuccess<CbOrbitLocation, OrPx4>, StReturnToBase, SUCCESS>
       >reactions;

     static void staticConfigure()
     {
       // center=(10,0), alt=5m, radius=5m, angular_vel=0.5 rad/s, 3 orbits
       configure_orthogonal<OrPx4, CbOrbitLocation>(
         10.0f, 0.0f, 5.0f, 5.0f, 0.5f, 3);
     }
   };

Signal Wiring End-to-End
~~~~~~~~~~~~~~~~~~~~~~~~~

The complete chain from state configuration to event:

1. **State** calls ``configure_orthogonal<OrPx4, CbGoToLocation>(10.0f, 0.0f, -5.0f)``
2. **CbGoToLocation::onEntry()** calls ``requiresComponent(goalChecker_)`` and ``requiresComponent(trajectorySetpoint_)``
3. **CbGoToLocation** sets the goal on ``CpGoalChecker`` and the setpoint on ``CpTrajectorySetpoint``
4. **CpGoalChecker::update()** (called at 20 Hz) compares current position vs goal
5. When within tolerance, ``CpGoalChecker`` fires ``onGoalReached_`` signal
6. **CbGoToLocation::onGoalReachedCallback()** calls ``postSuccessEvent()``
7. ``EvCbSuccess<CbGoToLocation, OrPx4>`` matches the transition → next state

Cross-Orthogonal Access
~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes a behavior needs data from a component on a **different** orthogonal. You can access any orthogonal's client and components through the state machine:

.. code-block:: c++

   void onEntry() override
   {
     // Access a component from a different orthogonal
     auto * otherClient = this->getStateMachine()
       ->getOrthogonal<OrOther>()
       ->getClient<ClOtherClient>();

     ClOtherComponent * comp;
     otherClient->requiresComponent(comp);
   }

|

Designing Your Own Multi-Stage Mission
---------------------------------------

When designing a complex mission:

1. **Identify the major phases** — these become mode states (e.g., Initialization, Active, Recovery, Shutdown)
2. **Break each phase into steps** — these become states within the mode state
3. **Identify repeating patterns** — these become super state loops
4. **Define recovery strategies** — use mode states with deep history transitions
5. **Assign orthogonals** — one per independent concern (navigation, manipulation, monitoring, etc.)

|

Summary
-------

You learned:

- How ``sm_multi_stage_1`` uses 5 modes with sequence super states for large-scale missions
- How ``sm_cl_px4_mr_test_1`` organizes a real flight mission into 6 flight-phase mode states
- The complete signal wiring chain from state configuration to event-driven transition
- Cross-orthogonal component access
- Design principles for multi-stage missions

|

Further Reading
---------------

- :doc:`/concepts/hsm-architecture` — Hierarchical state machine architecture
- :doc:`/concepts/substate-architecture` — Substates, orthogonals, events, components
- :doc:`/how-to/how-to-px4` — PX4 integration reference
- :doc:`/how-to/how-to-nav2` — Nav2 integration reference
