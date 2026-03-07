.. title:: Tutorial 9 — Super States
.. meta::
   :description: Use SMACC2 mode states and super states for hierarchical state grouping, inner state loops, and recovery modes.

Tutorial 9 — Super States
==========================

Real-world state machines quickly outgrow a flat list of states. SMACC2 supports **hierarchical state grouping** through mode states and super states, as demonstrated in the ``sm_three_some`` reference state machine. In this tutorial you will learn how to create mode states, super states with inner states, and loop patterns.

Mode States
-----------

A **mode state** is a top-level grouping of states, analogous to an operating mode. The ``sm_three_some`` state machine has two modes:

.. code-block:: c++

   // mode_states/ms_run.hpp
   struct MsRun : smacc2::SmaccState<MsRun, SmThreeSome, StState1>
   {
     using SmaccState::SmaccState;
   };

.. code-block:: c++

   // mode_states/ms_recover.hpp
   struct MsRecover : smacc2::SmaccState<MsRecover, SmThreeSome>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvToDeep, MsRun::deep_history>
       >reactions;
   };

Key points:

- ``SmaccState<MsRun, SmThreeSome, StState1>`` — the **third** template parameter is the **initial child state**. When the machine enters ``MsRun``, it immediately enters ``StState1``.
- States inside ``MsRun`` declare their parent as ``MsRun``, not ``SmThreeSome``.
- ``MsRecover`` transitions to ``MsRun::deep_history``, which returns to the last active state inside ``MsRun`` — deep history preserves the full state hierarchy.

The state machine declaration uses the mode state as its initial state:

.. code-block:: c++

   struct SmThreeSome
     : public smacc2::SmaccStateMachineBase<SmThreeSome, MsRun>
   {
     using SmaccStateMachineBase::SmaccStateMachineBase;

     virtual void onInitialize() override
     {
       this->createOrthogonal<OrTimer>();
       this->createOrthogonal<OrKeyboard>();
       this->createOrthogonal<OrSubscriber>();
     }
   };

Super States
------------

A **super state** groups related inner states into a reusable, self-contained unit. Super states use a namespace to prevent name collisions between inner states:

.. code-block:: c++

   // superstates/ss_superstate_1.hpp
   namespace SS1
   {
   // Forward declarations
   class StiState1;
   class StiState2;
   class StiState3;

   struct Ss1 : smacc2::SmaccState<Ss1, MsRun, StiState1>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvLoopEnd<Ss1>, SS2::Ss2>
       >reactions;

     static void staticConfigure()
     {
       configure_orthogonal<OrTimer, CbTimerCountdownOnce>(10);
       configure_orthogonal<OrSubscriber, CbWatchdogSubscriberBehavior>();
       configure_orthogonal<OrKeyboard, CbDefaultKeyboardBehavior>();
     }

     int iteration_count = 0;
     static constexpr int total_iterations() { return 5; }

     void runtimeConfigure() { iteration_count = 0; }
   };
   }  // namespace SS1

Key points:

- ``SmaccState<Ss1, MsRun, StiState1>`` — parent is ``MsRun``, initial inner state is ``StiState1``.
- The namespace ``SS1`` prevents inner state names (``StiState1``, etc.) from colliding with those in other super states.
- ``iteration_count`` and ``total_iterations()`` support the loop pattern.
- The super state's transition ``EvLoopEnd<Ss1>`` fires when the inner loop completes.

Inner States
~~~~~~~~~~~~

Inner states belong to their super state:

.. code-block:: c++

   // states/inner_states/sti_state_1.hpp
   namespace SS1
   {
   struct StiState1 : smacc2::SmaccState<StiState1, Ss1>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvLoopContinue<Ss1>, StiState2, CONTINUELOOP>
       >reactions;

     bool loopWhileCondition()
     {
       auto & ss = this->context<Ss1>();
       return ss.iteration_count++ < ss.total_iterations();
     }

     void onEntry()
     {
       RCLCPP_INFO(getLogger(), "Loop iteration: %d",
                   this->context<Ss1>().iteration_count);
       checkWhileLoopConditionAndThrowEvent(&StiState1::loopWhileCondition);
     }
   };
   }  // namespace SS1

The loop pattern:

1. ``StiState1::onEntry()`` calls ``checkWhileLoopConditionAndThrowEvent()``.
2. This evaluates ``loopWhileCondition()`` — if true, it posts ``EvLoopContinue``, transitioning to ``StiState2``.
3. The inner states cycle: ``StiState1 → StiState2 → StiState3 → StiState1``.
4. When ``loopWhileCondition()`` returns false (after 5 iterations), ``EvLoopEnd`` is posted.
5. The super state's transition table matches ``EvLoopEnd<Ss1>`` and exits the super state.

Accessing Super State Context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inner states access their super state's data through ``this->context<Ss1>()``:

.. code-block:: c++

   auto & ss = this->context<Ss1>();
   int count = ss.iteration_count;

This returns a reference to the live super state instance, so you can read and write its member variables.

Hierarchy Overview
------------------

The ``sm_three_some`` hierarchy looks like this:

.. code-block:: text

   SmThreeSome
   ├── MsRun (initial)
   │   ├── StState1 (initial child of MsRun)
   │   ├── StState2
   │   ├── StState3
   │   ├── StState4
   │   ├── SS1::Ss1 (super state)
   │   │   ├── StiState1 → StiState2 → StiState3 (loop × 5)
   │   │   └── EvLoopEnd → SS2::Ss2
   │   └── SS2::Ss2 (super state)
   │       ├── StiState1 → StiState2 → StiState3 (loop × 5)
   │       └── EvLoopEnd → StState4
   └── MsRecover
       └── EvToDeep → MsRun::deep_history

Transitions can cross hierarchy levels. A regular state inside ``MsRun`` can transition to a super state (``StState3 → SS1::Ss1``), and a super state can transition out to another super state (``SS1::Ss1 → SS2::Ss2``) or a regular state (``SS2::Ss2 → StState4``).

Summary
-------

You learned:

- **Mode states** group states into operational modes (``MsRun``, ``MsRecover``)
- **Super states** group inner states with namespaces for isolation
- The **loop pattern**: ``checkWhileLoopConditionAndThrowEvent()`` + ``EvLoopContinue`` / ``EvLoopEnd``
- **``this->context<Ss>()``** accesses parent super state data
- **Deep history** (``MsRun::deep_history``) restores the full state hierarchy on recovery

Next Steps
----------

In :doc:`tutorial-10-multi-stage-missions` you will combine all these concepts into a complete multi-stage autonomous mission.
