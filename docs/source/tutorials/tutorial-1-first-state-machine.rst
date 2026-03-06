.. title:: Tutorial 1 — Your First State Machine
.. meta::
   :description: Build, run, and understand sm_atomic — the simplest SMACC2 state machine — using a ROS2 timer client, two states, and the SMACC RTA viewer.

Tutorial 1 — Your First State Machine
======================================

In this tutorial you will clone the SMACC2 repository, build the **sm_atomic** state machine, run it, and walk through every source file to understand how SMACC2 state machines are structured.

Prerequisites
-------------

- ROS 2 Jazzy installed and sourced (see :doc:`/getting-started`)
- A colcon workspace (e.g. ``~/ros2_ws/``)

Build and Run sm_atomic
-----------------------

.. code-block:: bash

   # Source ROS 2
   source /opt/ros/jazzy/setup.bash

   # Clone SMACC2 into your workspace (skip if already cloned)
   cd ~/ros2_ws/src
   git clone https://github.com/robosoft-ai/SMACC2.git

   # Build only sm_atomic and its dependency
   cd ~/ros2_ws
   colcon build --packages-select sm_atomic cl_ros2_timer

   # Source the workspace
   source install/setup.bash

   # Launch the state machine
   ros2 launch sm_atomic sm_atomic.py

You should see log output showing the state machine cycling between **State1** and **State2**.

Project Structure
-----------------

.. code-block:: text

   sm_atomic/
   ├── include/sm_atomic/
   │   ├── sm_atomic.hpp            # State machine definition
   │   ├── orthogonals/
   │   │   └── or_timer.hpp         # Timer orthogonal
   │   └── states/
   │       ├── st_state_1.hpp       # State 1
   │       └── st_state_2.hpp       # State 2
   ├── src/sm_atomic/
   │   └── sm_atomic_node.cpp       # Entry point
   ├── launch/
   │   └── sm_atomic.py             # ROS 2 launch file
   ├── config/
   │   └── sm_atomic_config.yaml    # Parameters
   ├── CMakeLists.txt
   └── package.xml

The Entry Point
~~~~~~~~~~~~~~~

The node file boots ROS 2 and hands control to the SMACC2 runtime:

.. code-block:: c++

   // sm_atomic_node.cpp
   #include <sm_atomic/sm_atomic.hpp>

   int main(int argc, char ** argv)
   {
     rclcpp::init(argc, argv);
     smacc2::run<sm_atomic::SmAtomic>();
   }

``smacc2::run<>()`` creates the state machine, enters the initial state, and spins the ROS 2 node until shutdown.

The State Machine
~~~~~~~~~~~~~~~~~

.. code-block:: c++

   // sm_atomic.hpp
   #include <smacc2/smacc.hpp>

   // CLIENTS
   #include <cl_ros2_timer/cl_ros2_timer.hpp>

   // CLIENT BEHAVIORS
   #include <cl_ros2_timer/client_behaviors/cb_timer_countdown_loop.hpp>
   #include <cl_ros2_timer/client_behaviors/cb_timer_countdown_once.hpp>

   // ORTHOGONALS
   #include "orthogonals/or_timer.hpp"

   using namespace boost;
   using namespace smacc2;

   namespace sm_atomic
   {
   // STATE forward declarations
   class State1;
   class State2;

   // STATE_MACHINE
   struct SmAtomic : public smacc2::SmaccStateMachineBase<SmAtomic, State1>
   {
     using SmaccStateMachineBase::SmaccStateMachineBase;

     virtual void onInitialize() override { this->createOrthogonal<OrTimer>(); }
   };

   }  // namespace sm_atomic

   #include "states/st_state_1.hpp"
   #include "states/st_state_2.hpp"

Key points:

- ``SmaccStateMachineBase<SmAtomic, State1>`` — the first template parameter is the state machine itself (CRTP), the second is the **initial state**.
- ``onInitialize()`` creates all orthogonals. Orthogonals are created once and live for the entire state machine lifetime.
- State headers are included **after** the class definition so they can reference ``SmAtomic`` and the forward-declared state names.

The Orthogonal
~~~~~~~~~~~~~~

.. code-block:: c++

   // orthogonals/or_timer.hpp
   #include <chrono>
   #include <cl_ros2_timer/cl_ros2_timer.hpp>
   #include <smacc2/smacc.hpp>

   using namespace std::chrono_literals;

   namespace sm_atomic
   {
   class OrTimer : public smacc2::Orthogonal<OrTimer>
   {
   public:
     void onInitialize() override
     {
       auto client = this->createClient<cl_ros2_timer::ClRos2Timer>(1s);
     }
   };
   }  // namespace sm_atomic

- ``Orthogonal<OrTimer>`` uses CRTP to identify the orthogonal type at compile time.
- ``createClient<ClRos2Timer>(1s)`` creates a timer client that ticks every 1 second. The client lives as long as the state machine.

State 1
~~~~~~~

.. code-block:: c++

   // states/st_state_1.hpp
   #include <smacc2/smacc.hpp>

   namespace sm_atomic
   {
   using namespace cl_ros2_timer;
   using namespace smacc2::default_transition_tags;

   struct State1 : smacc2::SmaccState<State1, SmAtomic>
   {
     using SmaccState::SmaccState;

     // TRANSITION TABLE
     typedef mpl::list<

       Transition<EvTimer<CbTimerCountdownOnce, OrTimer>, State2, SUCCESS>

       >reactions;

     // STATE FUNCTIONS
     static void staticConfigure()
     {
       configure_orthogonal<OrTimer, CbTimerCountdownLoop>(3);
       configure_orthogonal<OrTimer, CbTimerCountdownOnce>(5);
     }

     void runtimeConfigure() {}

     void onEntry() { RCLCPP_INFO(getLogger(), "On Entry!"); }

     void onExit() { RCLCPP_INFO(getLogger(), "On Exit!"); }
   };
   }  // namespace sm_atomic

Walking through each piece:

- ``SmaccState<State1, SmAtomic>`` — first param is the state (CRTP), second is the parent (the state machine).
- **Transition table** — ``mpl::list`` of ``Transition<Event, TargetState, Tag>``. When ``EvTimer`` fires from ``CbTimerCountdownOnce`` on ``OrTimer``, the machine transitions to ``State2`` tagged ``SUCCESS``.
- ``staticConfigure()`` — called once at compile-time registration. It assigns **client behaviors** to orthogonals. Here, two behaviors run concurrently on ``OrTimer``: a countdown loop (fires every 3 ticks) and a countdown once (fires after 5 ticks).
- ``onEntry()`` / ``onExit()`` — called when the state is entered or exited.

State 2
~~~~~~~

.. code-block:: c++

   // states/st_state_2.hpp
   #include <smacc2/smacc.hpp>

   namespace sm_atomic
   {
   using namespace cl_ros2_timer;
   using namespace smacc2::default_transition_tags;

   struct State2 : smacc2::SmaccState<State2, SmAtomic>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<

       Transition<EvTimer<CbTimerCountdownOnce, OrTimer>, State1, SUCCESS>

       >reactions;

     static void staticConfigure()
     {
       configure_orthogonal<OrTimer, CbTimerCountdownOnce>(5);
     }

     void runtimeConfigure() { RCLCPP_INFO(getLogger(), "Entering State2"); }

     void onEntry() { RCLCPP_INFO(getLogger(), "On Entry!"); }

     void onExit() { RCLCPP_INFO(getLogger(), "On Exit!"); }
   };
   }  // namespace sm_atomic

State2 transitions back to State1 after 5 timer ticks, creating an infinite loop: **State1 → State2 → State1 → ...**

How It Works
------------

1. ``smacc2::run<SmAtomic>()`` creates the state machine and calls ``onInitialize()``, which creates ``OrTimer``.
2. The machine enters ``State1``. ``staticConfigure()`` attaches ``CbTimerCountdownLoop(3)`` and ``CbTimerCountdownOnce(5)`` to ``OrTimer``.
3. The timer client ticks every 1 second. After 5 ticks, ``CbTimerCountdownOnce`` fires ``EvTimer``.
4. The transition table matches the event and the machine transitions to ``State2``.
5. ``State1::onExit()`` runs, then ``State2::onEntry()`` runs.
6. State2 configures its own ``CbTimerCountdownOnce(5)`` and the cycle repeats.

Observing with the SMACC RTA
-----------------------------

The SMACC2 Runtime Analyzer (RTA) provides a live visualization of your state machine. While the state machine is running, you can connect to it at `robosoft.ai/viewer <https://robosoft.ai/viewer>`_ to see:

- The current active state
- State transition history
- Orthogonal and client behavior status

You can also inspect state machine status from the command line:

.. code-block:: bash

   ros2 topic echo /sm_atomic/smacc/status

Next Steps
----------

In :doc:`tutorial-2-adding-states-transitions` you will add a third state and learn about custom transition tags.
