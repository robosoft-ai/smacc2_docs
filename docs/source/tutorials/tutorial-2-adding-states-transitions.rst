.. title:: Tutorial 2 — Adding States and Transitions
.. meta::
   :description: Extend sm_atomic with a third state, wire multi-state transitions, and define custom transition tags like TIMEOUT and NEXT.

Tutorial 2 — Adding States and Transitions
===========================================

In this tutorial you will add a third state to **sm_atomic**, wire a three-state cycle, and learn how to use **custom transition tags** as seen in the ``sm_three_some`` reference state machine.

Starting Point
--------------

You should have a working ``sm_atomic`` build from :doc:`tutorial-1-first-state-machine`.

Step 1 — Add a Third State
---------------------------

Create the file ``include/sm_atomic/states/st_state_3.hpp``:

.. code-block:: c++

   // states/st_state_3.hpp
   #pragma once
   #include <smacc2/smacc.hpp>

   namespace sm_atomic
   {
   using namespace cl_ros2_timer;
   using namespace smacc2::default_transition_tags;

   struct State3 : smacc2::SmaccState<State3, SmAtomic>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<

       Transition<EvTimer<CbTimerCountdownOnce, OrTimer>, State1, SUCCESS>

       >reactions;

     static void staticConfigure()
     {
       configure_orthogonal<OrTimer, CbTimerCountdownOnce>(5);
     }

     void runtimeConfigure() {}

     void onEntry() { RCLCPP_INFO(getLogger(), "On Entry State3!"); }

     void onExit() { RCLCPP_INFO(getLogger(), "On Exit State3!"); }
   };
   }  // namespace sm_atomic

Step 2 — Forward-Declare and Include
-------------------------------------

In ``sm_atomic.hpp``, add the forward declaration and include:

.. code-block:: c++

   // Add forward declaration alongside State1 and State2
   class State1;
   class State2;
   class State3;  // NEW

.. code-block:: c++

   // Add include at the bottom
   #include "states/st_state_1.hpp"
   #include "states/st_state_2.hpp"
   #include "states/st_state_3.hpp"  // NEW

Step 3 — Wire the Three-State Cycle
------------------------------------

Update the transition tables so the machine cycles **State1 → State2 → State3 → State1**:

In ``st_state_1.hpp``, the transition already goes to State2 — no change needed.

In ``st_state_2.hpp``, change the target from ``State1`` to ``State3``:

.. code-block:: c++

   typedef mpl::list<

     Transition<EvTimer<CbTimerCountdownOnce, OrTimer>, State3, SUCCESS>

     >reactions;

In ``st_state_3.hpp``, the transition already goes back to ``State1``.

Rebuild and test:

.. code-block:: bash

   colcon build --packages-select sm_atomic
   source install/setup.bash
   ros2 launch sm_atomic sm_atomic.py

You should see the machine cycling through all three states.

Custom Transition Tags
----------------------

The default tags ``SUCCESS``, ``ABORT``, and ``CANCEL`` come from ``smacc2::default_transition_tags``. You can define your own tags to give transitions semantic meaning. The ``sm_three_some`` reference state machine demonstrates this pattern.

Define custom tags as structs that inherit from a default tag:

.. code-block:: c++

   // Custom transition tags
   struct TIMEOUT : ABORT {};
   struct NEXT : SUCCESS {};
   struct PREVIOUS : ABORT {};

These tags appear in the SMACC RTA viewer and in log output, making it easy to understand *why* a transition occurred.

Multiple Transitions in One State
----------------------------------

A single state can have multiple transitions in its ``mpl::list``. Each transition reacts to a different event. From ``sm_three_some``'s ``st_state_1.hpp``:

.. code-block:: c++

   typedef mpl::list<

     Transition<EvTimer<CbTimerCountdownOnce, OrTimer>, StState2, TIMEOUT>,
     Transition<EvTopicMessage<ClSubscriber, OrSubscriber>, StState2, TIMEOUT>,
     Transition<EvKeyPressP<CbDefaultKeyboardBehavior, OrKeyboard>, SS1::Ss1, PREVIOUS>,
     Transition<EvKeyPressN<CbDefaultKeyboardBehavior, OrKeyboard>, StState2, NEXT>,
     Transition<EvFail, MsRecover, ABORT>

     >reactions;

Key observations:

- **Multiple events** can trigger transitions from one state — the first matching event wins.
- Events are **typed** with the behavior and orthogonal that produced them: ``EvTimer<CbTimerCountdownOnce, OrTimer>``.
- Custom tags (``TIMEOUT``, ``NEXT``, ``PREVIOUS``) communicate intent to the RTA viewer.
- You can transition to states at different levels of the hierarchy (``SS1::Ss1`` is a superstate, ``MsRecover`` is a mode state).

Summary
-------

You learned how to:

- Add a new state to an existing state machine
- Wire multi-state transition cycles
- Define and use custom transition tags
- Configure multiple transitions in a single ``mpl::list``

Next Steps
----------

In :doc:`tutorial-3-orthogonals-concurrent-behaviors` you will add a second orthogonal to run concurrent behaviors alongside the timer.
