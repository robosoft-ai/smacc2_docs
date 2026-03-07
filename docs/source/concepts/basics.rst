.. title:: SMACC Basics
.. meta::
   :description: Foundational SMACC2 concepts including state functions, transitions, function call order, naming conventions, folder structures, threading model, and signal-based communication.

SMACC Basics
============

SMACC States
------------

**State Functions**

- staticConfigure() -- For static configuration of orthogonals.
- runtimeConfigure() -- For runtime configuration of orthogonals.
- onEntry() -- For RT Steady State. Here it is assumed that everything has been configured, and you are ready to roll.
- update()
- onExit() -- Self explanatory

Transitions
-----------

In 2003, David Abrams, founder of the Boost Libraries, Author of boost.mpl and Aleksey Gurtovoy, wrote an example for their MPL library that encompassed a state machine (procedural) and the first Transition Table. Seen below...


.. image:: /images/boost-mpl-transition-table-3-Cropped.jpg
    :width: 700px
    :align: center


https://www.boost.org/doc/libs/1_72_0/libs/mpl/example/fsm/player1.cpp

This table, was extremely popular and was adopted almost unchanged into other state machine libraries such as boost.MSM.

In the boost.MPL library, only procedural state machines could be written, and the transition table was for the entire state machine.

In SMACC we've adapted the Transition Table to the behavioral state machine (along with Boost Statechart) by including a transition table inside of every state.

Order of Function Calls
-----------------------

In SMACC States, the standard function calls are....

- staticConfigure()
- runtimeConfigure()
- onEntry()
- update()* -- Must be added explicitly
- onExit()

In the client behaviors, the standard function calls are...

- runtimeConfigure()
- onEntry()
- update()* -- Must be added explicitly
- onExit()

So, lets assume that we have a state machine (SmExample) with two orthogonals (OrOne & OrTwo), in state StOne, with one client, and one client behavior in each orthogonal (ClOne, ClTwo, CbOne, CbTwo).

From the state StOne, the order of the function calls would be...

- StOne -- staticConfigure()
- StOne -- runtimeConfigure()
- CbOne -- runtimeConfigure()
- CbTwo -- runtimeConfigure()
- StOne -- onEntry()
- CbOne -- onEntry()
- CbTwo -- onEntry()
- CbOne -- update()*
- CbTwo -- update()*
- StOne -- update()*
- CbOne -- onExit()
- CbTwo -- onExit()
- StOne -- onExit()

Naming Convention
-----------------

Because of the complexities of c++ template code and state machines in general, the Authors of the SMACC library developed a naming convention that users are strongly encouraged to follow.

**Benefits of Adopting the Convention**

The first benefit, is that the convention greatly improves code readability, especially from inside an IDE or the SMACC doxygen pages.

The second benefit, is that if you run into issues, the SMACC support team can quickly and easily get a handle on the broader picture of your problem.

And the third benefit, is that the SMACC development tools, such as the SMACC Viewer and the yet-to-be-built code-generator will utilize this same naming convention and by adopting it, you ensure compatibility.

**Prefixes**

Header files have the following format...

- ``sm_`` = state machine (ex: sm_dance_bot.h)
- ``ms_`` = mode state (ex: ms_recover.h)
- ``ss_`` = super state (ex: ss_sequence_1.h)
- ``st_`` = state (ex: st_navigate_to_waypoints_x.h)
- ``sti_`` = inner state (ex: sti_radial_rotate.h)
- ``sr_`` = state reactor (ex: sr_all_events_go.h)
- ``or_`` = orthogonal (ex: or_navigation.h)
- ``cl_`` = client (ex: cl_move_base_z.h)
- ``cb_`` = client behavior (ex: cb_timeout_watchdog.h)
- ``cp_`` = component (ex: cp_odom_tracker.h)
- ``ev_`` = event (ex: ev_navigation_success.h)

And then classes have the following format...

- Sm = state machine (ex: SmDanceBot)
- Ms = mode state (ex: MsRecover)
- Ss = super state (ex: SsSequence1)
- St = state (ex: StNavigateToWaypointsX)
- Sti = inner state (ex: StiRadialRotate)
- Sr = state reactor (ex: SrAllEventsGo)
- Or = orthogonal (ex: OrNavigation)
- Cl = client (ex: ClMoveBaseZ)
- Cb = client behavior (ex: CbTimeoutWatchdog)
- Cp = component (ex: CpOdomTracker)
- Ev = event (ex: EvNavigationSuccess)

State Machine Folder Structure
------------------------------

**Example State Machine Folder Structure**

.. code-block:: text

   sm_example/
   ├── CMakeLists.txt
   ├── package.xml
   ├── config/
   ├── docs/
   ├── include/
   │   └── sm_example/
   │       ├── orthogonals/
   │       │   └── or_navigation.hpp
   │       ├── states/
   │       │   ├── st_state_1.hpp
   │       │   └── st_state_2.hpp
   │       ├── superstates/
   │       │   └── ss_superstate_1.hpp
   │       ├── modestates/
   │       │   └── ms_run_mode.hpp
   │       └── sm_example.hpp
   ├── launch/
   │   └── sm_example.launch.py
   └── src/
       └── sm_example/
           └── sm_example_node.cpp

The ``include/sm_example/sm_example.hpp`` header is the main state machine definition, and ``src/sm_example/sm_example_node.cpp`` contains the ``main()`` entry point.

Client Library Folder Structure
-------------------------------

**Example Client Library Folder Structure**

.. code-block:: text

   cl_example/
   ├── CMakeLists.txt
   ├── package.xml
   ├── include/
   │   └── cl_example/
   │       ├── cl_example.hpp
   │       ├── client_behaviors/
   │       │   ├── cb_behavior_1.hpp
   │       │   └── cb_behavior_2.hpp
   │       └── components/
   │           ├── cp_component_1.hpp
   │           └── cp_component_2.hpp
   └── src/
       └── cl_example/
           ├── cl_example.cpp
           ├── client_behaviors/
           │   ├── cb_behavior_1.cpp
           │   └── cb_behavior_2.cpp
           └── components/
               ├── cp_component_1.cpp
               └── cp_component_2.cpp

The client library compiles into a shared library (``.so``) that state machines link against at build time.

Threading Model
---------------

**State Machine Event Processing**

SMACC is built on the Boost StateChart library and consequently shares many similarities with that library.  The StateChart library provides synchronous and asynchronous threading models with which one can build a state machine. The synchronous model unsurprisingly creates synchronous state machines. Synchronous threads are simpler to understand and reason about, since they process input events as they come in. However, only one event can be processed at a time and if another event is triggered, the event currently being processed may be pre-empted and have its computation disrupted. This would lead to erratic behaviour. Robotics applications are typically very complex machines with many sensor inputs that need to be processed and control outputs that need to be generated.

Asynchronous threads are substantially more complex to reason about and manage, but offer greater flexibility. Primarily for this reason, asynchronous threading is used in SMACC. Asynchronous threads are implemented with two main components: a scheduler and the processor. The scheduler receives events from external clients and stores them in a queue to be processed by the processor. Schedulers may feed the processor events based on some selection scheme, e.g. priority or a deadline. SMACC uses a FIFO (first in, first out) scheduler to process its events. When the scheduler's event queue is empty, the processor will idle until new events are fed.

Updateability
-------------

**Updateable Class**

SMACC signals are an extension to the Boost.Signals2 object and is a thread-safe implementation of the signals and slots design construct. Signals and slots allow for the observer pattern to be easily implemented safely without excessive boilerplate code. In this case, the signal is the event emitter that can have multiple subscribers attached to it. When an event is emitted as a callback, the attached slots receive the event and execute their function. The signals and slots construct is a good fit for SMACC, which has to subscribe to a ROS topic (i.e. a signal) and execute some code when a new message is received (i.e. execute a slot).

**Why SmaccSignal instead of raw Boost.Signals2?**

SMACC wraps Boost.Signals2 in its own SmaccSignal type for a critical reason: automatic lifecycle management. The state machine tracks all signal connections by object pointer through its ``createSignalConnection()`` mechanism. When a state-scoped object (such as a client behavior) is destroyed on state exit, the framework automatically calls ``disconnectSmaccSignalObject()`` to sever all of that object's signal connections.

Without this, using raw Boost.Signals2 would lead to serious problems:

- **Dangling callbacks:** A client behavior subscribes to a client's signal in ``onEntry()``. The state exits and the behavior is destroyed, but the raw signal connection persists. When the client fires the signal, it invokes a callback on a destroyed object -- a segmentation fault.
- **Orphaned connections:** Each state transition would accumulate dead connections that are never cleaned up, leaking memory over the lifetime of the state machine.
- **Stale events:** Without the framework's ``EventLifeTime::CURRENT_STATE`` enforcement, an asynchronous client behavior could post events into the wrong state after a transition has already occurred, corrupting the state machine's execution flow.

The SmaccSignal approach is not just convenience -- it is essential for correctness in a system where objects are continuously created and destroyed across state transitions.
