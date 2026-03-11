.. title:: Tutorial 8 — Events and State Reactors
.. meta::
   :description: Define custom events, use typed events, and combine multiple events with state reactors like SrAllEventsGo for complex SMACC2 transition logic.

Tutorial 8 — Events and State Reactors
=======================================

Events drive every state transition in SMACC2. In the basic tutorials you used framework-provided events like ``EvTimer`` and ``EvCbSuccess``. In this tutorial you will learn to define **custom events**, understand **typed events**, and use **state reactors** to combine multiple events into complex transition logic.

Custom Events
-------------

Define a custom event as a struct inheriting from ``sc::event<>``:

.. code-block:: c++

   // In sm_three_some.hpp
   struct EvToDeep : sc::event<EvToDeep> {};
   struct EvFail : sc::event<EvFail> {};

Custom events are simple — they carry no template parameters and no data. They are useful for cross-state signaling, error handling, and mode switching.

Use them in a transition table:

.. code-block:: c++

   typedef mpl::list<
     Transition<EvFail, MsRecover, ABORT>
     >reactions;

Any code with access to the state machine can post a custom event:

.. code-block:: c++

   this->postEvent<EvFail>();

Typed Events
------------

Most SMACC2 events are **typed** — they carry template parameters identifying their source behavior and orthogonal:

.. code-block:: c++

   EvTimer<CbTimerCountdownOnce, OrTimer>
   EvCbSuccess<CbArmPX4, OrPx4>
   EvKeyPressN<CbDefaultKeyboardBehavior, OrKeyboard>
   EvTopicMessage<ClSubscriber, OrSubscriber>

The type parameters serve two purposes:

1. **Disambiguation** — when multiple orthogonals could fire the same event type, the orthogonal parameter tells the transition table exactly which one to match.
2. **Traceability** — the RTA viewer and logs show exactly which behavior on which orthogonal produced the event.

You define your own typed events the same way:

.. code-block:: c++

   template <typename TSource, typename TOrthogonal>
   struct EvHttp : sc::event<EvHttp<TSource, TOrthogonal>> {};

The event is then posted using ``onStateOrthogonalAllocation<>()`` which captures the type parameters at compile time (see :doc:`tutorial-3-orthogonals-concurrent-behaviors` for the ``CbHttpRequest`` example).

State Reactors
--------------

A **state reactor** watches for multiple events and fires a single output event when a condition is met. This is useful when a state needs to wait for several things to happen before transitioning.

SrAllEventsGo
~~~~~~~~~~~~~

``SrAllEventsGo`` waits for **all** specified events to arrive, then fires its output event. From ``sm_three_some``'s ``st_state_2.hpp``:

.. code-block:: c++

   struct StState2 : smacc2::SmaccState<StState2, MsRun>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvTimer<CbTimerCountdownOnce, OrTimer>, StState3, TIMEOUT>,
       Transition<EvAllGo<SrAllEventsGo>, StState3>,
       Transition<EvKeyPressP<CbDefaultKeyboardBehavior, OrKeyboard>,
                  StState1, PREVIOUS>,
       Transition<EvKeyPressN<CbDefaultKeyboardBehavior, OrKeyboard>,
                  StState3, NEXT>
       >reactions;

     static void staticConfigure()
     {
       configure_orthogonal<OrTimer, CbTimerCountdownOnce>(10);
       configure_orthogonal<OrSubscriber, CbWatchdogSubscriberBehavior>();
       configure_orthogonal<OrKeyboard, CbDefaultKeyboardBehavior>();

       // State reactor: wait for keys A, B, and C to all be pressed
       static_createStateReactor<
         SrAllEventsGo,
         EvAllGo<SrAllEventsGo>,
         mpl::list<
           EvKeyPressA<CbDefaultKeyboardBehavior, OrKeyboard>,
           EvKeyPressB<CbDefaultKeyboardBehavior, OrKeyboard>,
           EvKeyPressC<CbDefaultKeyboardBehavior, OrKeyboard>
         >
       >();
     }
   };

How it works:

1. ``SrAllEventsGo`` is created with a list of **input events** (A, B, C key presses).
2. As each input event arrives, the reactor marks it as received.
3. When **all** input events have been received, it posts the **output event** ``EvAllGo<SrAllEventsGo>``.
4. The transition table matches ``EvAllGo`` and transitions to ``StState3``.

The reactor coexists with other transitions — the timer timeout at 10 seconds is a fallback that fires regardless of the reactor.

Other State Reactors
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Reactor
     - Behavior
   * - ``SrAllEventsGo``
     - Fires output when **all** input events received
   * - ``SrConditional``
     - Fires one of two output events based on a boolean condition
   * - ``SrEventCountdown``
     - Fires output after receiving N occurrences of an event

Creating a State Reactor
~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``static_createStateReactor<>()`` in ``staticConfigure()``:

.. code-block:: c++

   static_createStateReactor<
     ReactorType,        // e.g. SrAllEventsGo
     OutputEvent,        // e.g. EvAllGo<SrAllEventsGo>
     mpl::list<InputEvents...>  // events to watch
   >();

The reactor is **state-scoped** — it is created when the state is entered and destroyed when the state exits.

Summary
-------

You learned:

- Custom events: ``struct EvFail : sc::event<EvFail> {}``
- Typed events with ``<TSource, TOrthogonal>`` template parameters for disambiguation
- State reactors that combine multiple events into complex transition logic
- ``SrAllEventsGo``, ``SrConditional``, and ``SrEventCountdown``
- ``static_createStateReactor<>()`` for declaring reactors in ``staticConfigure()``

Next Steps
----------

In :doc:`tutorial-9-hierarchical-states` you will learn how to group states into hierarchical states with mode states, super states, and loop control.
