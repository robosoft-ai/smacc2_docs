.. title:: HSM Architecture
.. meta::
   :description: Hierarchical state machine architecture in SMACC2, covering hierarchical states, mode states, super states, inner state loops, deep history, and state-local storage.

HSM Architecture
================

Hierarchical States
-------------------

Let's talk about SMACC support for hierarchical states...

.. image:: /images/SMACC-State-Hierarchy.jpg
    :width: 700px
    :align: center

We need to make a distinction between parent states & leaf states. Leaf states being defined as those states that do not have any child states. In the example above, StState1, StState2, StiState1, StiState2 and StiState3 are leaf states.

As can be seen in the image above, only leaf states should have orthogonals. The reason for this being that only the leaf states interact with the hardware interface, where the higher level parent states such as superstates and modestates, define sequences of states, looping of states, parameter changes, etc.

SMACC2 provides three levels of hierarchy above leaf states:

- **Mode States (Ms)** -- top-level groupings that represent operational phases of the state machine (e.g., ``MsRun``, ``MsRecover``, ``MsInFlight``).
- **Super States (Ss)** -- mid-level groupings that define repeatable sequences or sub-phases within a mode state.
- **Inner States (Sti)** -- leaf states that live inside a super state and participate in loops and sequences.

The sections below explain each level in detail.

Mode States
-----------

A mode state is the highest level of hierarchy inside a state machine. It groups related states into a named operational phase and specifies which child state to enter first.

**Template signature:**

.. code-block:: c++

   struct MsRun : smacc2::SmaccState<MsRun, SmThreeSome, StState1>

The three template parameters are:

1. The mode state itself (``MsRun``)
2. The parent -- always the state machine (``SmThreeSome``)
3. The initial child state (``StState1``) -- the state entered when the mode state is activated

**Example -- sm_three_some: MsRun and MsRecover**

``sm_three_some`` uses two mode states to separate normal execution from error recovery:

.. code-block:: c++

   // ms_run.hpp -- normal execution mode
   class MsRun : public smacc2::SmaccState<MsRun, SmThreeSome, StState1>
   {
   public:
     using SmaccState::SmaccState;
   };

.. code-block:: c++

   // ms_recover.hpp -- recovery mode
   class MsRecover : public smacc2::SmaccState<MsRecover, SmThreeSome>
   {
   public:
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvToDeep, smacc2::deep_history<typename MsRun::LastDeepState>, SUCCESS>
       >reactions;
   };

The state machine itself declares ``MsRun`` as its initial state:

.. code-block:: c++

   struct SmThreeSome : public smacc2::SmaccStateMachineBase<SmThreeSome, MsRun>
   {
     using SmaccStateMachineBase::SmaccStateMachineBase;

     void onInitialize() override
     {
       this->createOrthogonal<OrTimer>();
       this->createOrthogonal<OrKeyboard>();
       this->createOrthogonal<OrSubscriber>();
     }
   };

**Example -- sm_cl_px4_mr_test_1: Flight phases as mode states**

A PX4 multirotor mission uses six mode states to represent distinct flight phases:

.. code-block:: c++

   // State machine with MsDisarmedOnGround as initial mode state
   struct SmClPx4MrTest1
     : public smacc2::SmaccStateMachineBase<SmClPx4MrTest1, MsDisarmedOnGround>
   { ... };

   // Each flight phase is a mode state with its own initial child
   struct MsDisarmedOnGround
     : smacc2::SmaccState<MsDisarmedOnGround, SmClPx4MrTest1, StWaitForReady> { ... };

   struct MsArmedOnGround
     : smacc2::SmaccState<MsArmedOnGround, SmClPx4MrTest1, StArmPx4> { ... };

   struct MsTakeoff
     : smacc2::SmaccState<MsTakeoff, SmClPx4MrTest1, StTakeoff> { ... };

   struct MsInFlight
     : smacc2::SmaccState<MsInFlight, SmClPx4MrTest1, StGoToWaypoint1> { ... };

   struct MsLanding
     : smacc2::SmaccState<MsLanding, SmClPx4MrTest1, StLand> { ... };

   struct MsLanded
     : smacc2::SmaccState<MsLanded, SmClPx4MrTest1, StLanded> { ... };

Mode-to-mode transitions are triggered by leaf states posting events that bubble up to the mode state level. For example, when ``StWaitForReady`` posts a timer event, the transition table at the mode state or leaf state level catches it and transitions to ``MsArmedOnGround``.

Super States
------------

Super states group a set of inner states into a reusable, namespaced unit inside a mode state. They are the mechanism for defining sequences, loops, and sub-phases within a mode.

**Namespace isolation pattern:**

Super states use a namespace to isolate their inner state forward declarations from other super states that may have identically named inner states (e.g., both ``SS1`` and ``SS2`` can each contain an ``StiState1``):

.. code-block:: c++

   // In sm_three_some.hpp -- forward declarations
   namespace SS1 { class Ss1; }
   namespace SS2 { class Ss2; }

**Super state definition:**

.. code-block:: c++

   // ss_superstate_1.hpp
   namespace sm_three_some
   {
   namespace SS1
   {
   namespace sm_three_some { namespace inner_states {
   class StiState1;
   class StiState2;
   class StiState3;
   }}

   using namespace sm_three_some::inner_states;

   struct Ss1 : smacc2::SmaccState<Ss1, MsRun, StiState1>
   {
   public:
     using SmaccState::SmaccState;

     // TRANSITION TABLE
     typedef mpl::list<
       Transition<EvLoopEnd<StiState1>, SS2::Ss2>
       >reactions;

     // STATE VARIABLES
     static constexpr int total_iterations() { return 5; }
     int iteration_count = 0;
   };

   using SS = SS1::Ss1;

   #include <sm_three_some/states/inner_states/sti_state_1.hpp>
   #include <sm_three_some/states/inner_states/sti_state_2.hpp>
   #include <sm_three_some/states/inner_states/sti_state_3.hpp>

   } // namespace SS1
   } // namespace sm_three_some

Key points:

- ``SmaccState<Ss1, MsRun, StiState1>`` -- the parent is the mode state ``MsRun``, and the initial child is ``StiState1``.
- ``iteration_count`` and ``total_iterations()`` are member variables on the super state that survive inner state transitions (see :ref:`state-local-storage` below).
- The ``using SS = SS1::Ss1`` alias lets inner states refer to their parent generically, enabling the same inner state code to be reused across multiple super states.
- When the loop ends (``EvLoopEnd<StiState1>``), the super state transitions to the next super state (``SS2::Ss2``) or back to a regular state.

Inner States and Loops
----------------------

Inner states (prefix ``Sti``) are leaf states that live inside a super state. They form the steps of a sequence or loop.

**Loop mechanism:**

SMACC2 provides built-in loop support through three elements:

1. ``loopWhileCondition()`` -- a method on an inner state that returns ``true`` to continue looping or ``false`` to end.
2. ``checkWhileLoopConditionAndThrowEvent()`` -- called in ``onEntry()`` to evaluate the condition and post the appropriate event.
3. ``EvLoopContinue`` / ``EvLoopEnd`` -- the events posted based on the condition.

**Example -- StiState1 as a loop gate:**

.. code-block:: c++

   // sti_state_1.hpp
   struct StiState1 : smacc2::SmaccState<StiState1, SS>
   {
   public:
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvLoopContinue<StiState1>, StiState2, CONTINUELOOP>
       >reactions;

     static void staticConfigure() {}
     void runtimeConfigure() {}

     bool loopWhileCondition()
     {
       auto & superstate = this->context<SS>();

       RCLCPP_INFO(
         getLogger(), "Loop start, current iterations: %d, total iterations: %d",
         superstate.iteration_count, superstate.total_iterations());
       return superstate.iteration_count++ < superstate.total_iterations();
     }

     void onEntry()
     {
       RCLCPP_INFO(getLogger(), "LOOP START ON ENTRY");
       checkWhileLoopConditionAndThrowEvent(&StiState1::loopWhileCondition);
     }
   };

How the loop works:

1. ``StiState1`` is entered (it is the initial child of the super state).
2. ``onEntry()`` calls ``checkWhileLoopConditionAndThrowEvent()``, which calls ``loopWhileCondition()``.
3. If ``iteration_count < total_iterations()``, ``EvLoopContinue<StiState1>`` is posted, transitioning to ``StiState2``.
4. ``StiState2`` does its work, transitions to ``StiState3``, which transitions back to ``StiState1``.
5. On the next entry of ``StiState1``, the iteration count is checked again. When the limit is reached, ``EvLoopEnd<StiState1>`` is posted.
6. The super state's transition table catches ``EvLoopEnd`` and transitions to the next super state or state.

The ``this->context<SS>()`` call accesses the parent super state, allowing inner states to read and write the super state's member variables -- this is how the iteration counter is shared across inner state transitions.

Deep History
------------

Deep history is a mechanism that allows a mode state to remember the exact nested state hierarchy it was in when it was exited, and restore that hierarchy when re-entered.

In SMACC2, deep history is accessed through ``ModeState::LastDeepState``:

.. code-block:: c++

   // ms_recover.hpp
   class MsRecover : public smacc2::SmaccState<MsRecover, SmThreeSome>
   {
   public:
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvToDeep, smacc2::deep_history<typename MsRun::LastDeepState>, SUCCESS>
       >reactions;
   };

**How it works:**

1. The state machine is in ``MsRun``, deep inside a nested hierarchy -- for example, ``MsRun > SS1::Ss1 > StiState2``.
2. An error event (``EvFail``) triggers a transition to ``MsRecover``.
3. ``MsRun`` is exited (along with all its nested states), but SMACC2 records the deepest active state as ``MsRun::LastDeepState``.
4. Inside ``MsRecover``, recovery logic runs (a recovery sequence, operator intervention, etc.).
5. When recovery is complete, ``EvToDeep`` is posted.
6. The transition target ``smacc2::deep_history<typename MsRun::LastDeepState>`` tells SMACC2 to re-enter ``MsRun`` and restore the full nested hierarchy, returning to ``StiState2`` inside ``SS1::Ss1``.

**Use case -- recovery modes:**

Deep history is essential for fault recovery in autonomous systems. Instead of restarting a mission from the beginning after a recoverable error, the state machine can:

1. Exit to a recovery mode state
2. Perform corrective actions (re-arm, re-calibrate, wait for operator input)
3. Resume exactly where it left off

This pattern is used extensively in ``sm_multi_stage_1``, which has dedicated ``MsRecovery1`` and ``MsRecovery2`` mode states that use deep history to return to the last active state inside the operational modes.

.. _state-local-storage:

State-Local Storage
-------------------

In SMACC2, leaf states and their client behaviors are destroyed on every state transition. This makes them unsuitable for storing data that must persist across multiple steps in a sequence. Mode states and super states solve this problem -- they survive inner state transitions and can hold member variables that inner states access through ``this->context<>()``.

**Super state as data holder:**

.. code-block:: c++

   struct Ss1 : smacc2::SmaccState<Ss1, MsRun, StiState1>
   {
     // These survive across StiState1 → StiState2 → StiState3 transitions
     static constexpr int total_iterations() { return 5; }
     int iteration_count = 0;
   };

**Accessing parent state data from a child:**

.. code-block:: c++

   // Inside any inner state of Ss1
   void onEntry()
   {
     auto & superstate = this->context<SS>();
     int current = superstate.iteration_count;

     // Read or write any member variable on the super state
     superstate.iteration_count++;
   }

**Mode state as data holder:**

The same pattern works at the mode state level. A mode state can store data that persists across all its child states, super states, and inner states:

.. code-block:: c++

   struct MsInFlight
     : smacc2::SmaccState<MsInFlight, SmClPx4MrTest1, StGoToWaypoint1>
   {
     using SmaccState::SmaccState;

     // Data accessible to all child states via this->context<MsInFlight>()
     int waypoints_completed = 0;
     float total_distance_flown = 0.0f;
   };

   // Inside a child state
   void onEntry()
   {
     auto & flight = this->context<MsInFlight>();
     flight.waypoints_completed++;
   }

**Contrast with state-scoped data:**

- **State member variables** -- destroyed on every state transition. Use for state-specific configuration and temporary data.
- **Client behavior member variables** -- destroyed on every state transition. Use for behavior-specific runtime state.
- **Super state member variables** -- survive inner state transitions within the super state. Use for loop counters, accumulated results, and sequence-level data.
- **Mode state member variables** -- survive all state transitions within the mode. Use for phase-level data like mission progress.
- **Component member variables** -- survive for the entire state machine lifetime. Use for persistent sensor data, connection state, and hardware interfaces.
