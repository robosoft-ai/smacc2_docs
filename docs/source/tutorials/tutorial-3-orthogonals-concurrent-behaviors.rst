.. title:: Tutorial 3 — Orthogonals and Concurrent Behaviors
.. meta::
   :description: Add a second orthogonal to run concurrent behaviors. Walk through sm_atomic_http which uses both a timer and an HTTP client in parallel.

Tutorial 3 — Orthogonals and Concurrent Behaviors
==================================================

Orthogonals let you run **independent behaviors in parallel**. Each orthogonal owns a client, and every state can configure behaviors on each orthogonal simultaneously. In this tutorial you will study the **sm_atomic_http** reference state machine, which uses two orthogonals — a timer and an HTTP client — running concurrently.

Prerequisites
-------------

- Completed :doc:`tutorial-1-first-state-machine`

Build and Run sm_atomic_http
-----------------------------

.. code-block:: bash

   cd ~/ros2_ws
   colcon build --packages-select sm_atomic_http cl_ros2_timer cl_http
   source install/setup.bash
   ros2 launch sm_atomic_http sm_atomic_http.py

The State Machine
-----------------

.. code-block:: c++

   // sm_atomic_http.hpp
   #include <smacc2/smacc.hpp>

   // CLIENTS
   #include <cl_ros2_timer/cl_ros2_timer.hpp>

   // CLIENT BEHAVIORS
   #include <cl_ros2_timer/client_behaviors/cb_timer_countdown_loop.hpp>
   #include <cl_ros2_timer/client_behaviors/cb_timer_countdown_once.hpp>
   #include "clients/client_behaviors/cb_http_request.hpp"

   // ORTHOGONALS
   #include "orthogonals/or_timer.hpp"
   #include "orthogonals/or_http.hpp"

   using namespace boost;
   using namespace smacc2;

   namespace sm_atomic_http {

   class State1;
   class State2;

   struct SmAtomicHttp
       : public smacc2::SmaccStateMachineBase<SmAtomicHttp, State1> {
     using SmaccStateMachineBase::SmaccStateMachineBase;

     virtual void onInitialize() override {
       this->createOrthogonal<OrTimer>();
       this->createOrthogonal<OrHttp>();
     }
   };

   }  // namespace sm_atomic_http

   #include "states/st_state_1.hpp"
   #include "states/st_state_2.hpp"

Two orthogonals are created in ``onInitialize()``. They run independently and concurrently.

The HTTP Orthogonal
~~~~~~~~~~~~~~~~~~~

.. code-block:: c++

   // orthogonals/or_http.hpp
   #pragma once

   #include <cl_http/cl_http.hpp>
   #include <smacc2/smacc.hpp>

   namespace sm_atomic_http {
   class OrHttp : public smacc2::Orthogonal<OrHttp> {
   public:
     void onInitialize() override {
       auto cl_http =
           this->createClient<cl_http::ClHttp>("https://example.com");
     }
   };
   }  // namespace sm_atomic_http

The HTTP client is initialized with a base URL. Like all clients, it lives for the entire state machine lifetime.

State 1 — Timer Countdown
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c++

   // states/st_state_1.hpp
   namespace sm_atomic_http {
   using namespace cl_ros2_timer;
   using namespace smacc2::default_transition_tags;

   struct State1 : smacc2::SmaccState<State1, SmAtomicHttp> {
     using SmaccState::SmaccState;

     typedef mpl::list<
         Transition<EvTimer<CbTimerCountdownOnce, OrTimer>, State2, SUCCESS> >
         reactions;

     static void staticConfigure() {
       configure_orthogonal<OrTimer, CbTimerCountdownOnce>(5);
     }

     void runtimeConfigure() {}

     void onEntry() { RCLCPP_INFO(getLogger(), "On Entry!"); }

     void onExit() { RCLCPP_INFO(getLogger(), "On Exit!"); }
   };
   }  // namespace sm_atomic_http

State1 only uses the timer orthogonal. After 5 ticks the machine transitions to State2.

State 2 — HTTP Request
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c++

   // states/st_state_2.hpp
   namespace sm_atomic_http {

   struct State2 : smacc2::SmaccState<State2, SmAtomicHttp> {
     using SmaccState::SmaccState;

     typedef mpl::list<
         Transition<EvHttp<CbHttpRequest, OrHttp>, State1, SUCCESS>>
         reactions;

     static void staticConfigure() {
       configure_orthogonal<OrHttp, CbHttpRequest>();
     }

     void runtimeConfigure() { RCLCPP_INFO(getLogger(), "Entering State2"); }

     void onEntry() { RCLCPP_INFO(getLogger(), "On Entry!"); }

     void onExit() { RCLCPP_INFO(getLogger(), "On Exit!"); }
   };
   }  // namespace sm_atomic_http

State2 uses the HTTP orthogonal. ``CbHttpRequest`` fires an ``EvHttp`` event when it receives a response, triggering the transition back to State1.

The HTTP Client Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c++

   // clients/client_behaviors/cb_http_request.hpp
   #pragma once

   #include <cl_http/client_behaviors/cb_http_get_request.hpp>
   #include <smacc2/smacc.hpp>

   namespace sm_atomic_http {

   template <typename TSource, typename TOrthogonal>
   struct EvHttp : sc::event<EvHttp<TSource, TOrthogonal>>
   {};

   class CbHttpRequest : public cl_http::CbHttpGetRequest {
   public:
     template <typename TOrthogonal, typename TSourceObject>
     void onStateOrthogonalAllocation() {
       triggerTranstition = [this]() {
         auto event = new EvHttp<TSourceObject, TOrthogonal>();
         this->postEvent(event);
       };
     }

     void onResponseReceived(const cl_http::ClHttp::TResponse & response) {
       RCLCPP_INFO_STREAM(this->getLogger(), "ON RESPONSE");
       RCLCPP_INFO_STREAM(this->getLogger(), response.body());
       triggerTranstition();
     }

   private:
     std::function<void()> triggerTranstition;
   };
   }  // namespace sm_atomic_http

This demonstrates a custom **typed event**: ``EvHttp<TSource, TOrthogonal>`` carries the source behavior and orthogonal type so that transition tables can match it precisely.

How Concurrent Behaviors Work
------------------------------

When a state is entered:

1. SMACC2 reads the ``staticConfigure()`` assignments.
2. For **each orthogonal**, the assigned behavior's ``onEntry()`` is called.
3. All behaviors across all orthogonals run **concurrently**.
4. When any behavior fires an event that matches a transition, the machine transitions — calling ``onExit()`` on all active behaviors.

Both orthogonals operate independently. In State1, only ``OrTimer`` has an assigned behavior, so ``OrHttp`` is idle. In State2, only ``OrHttp`` has a behavior, so ``OrTimer`` is idle. You can also configure **both orthogonals** in a single state to have them run side by side.

Configuring Both Orthogonals in One State
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can assign behaviors to multiple orthogonals in the same ``staticConfigure()``:

.. code-block:: c++

   static void staticConfigure() {
     configure_orthogonal<OrTimer, CbTimerCountdownOnce>(5);
     configure_orthogonal<OrHttp, CbHttpRequest>();
   }

Both behaviors start when the state is entered and run concurrently. The first event to match a transition wins.

Summary
-------

You learned:

- How to create multiple orthogonals for concurrent behavior execution
- That each orthogonal owns one client and can have behaviors assigned per state
- How typed events (``EvHttp<TSource, TOrthogonal>``) enable precise transition matching
- That all behaviors on all orthogonals run concurrently within a state

Next Steps
----------

In :doc:`tutorial-4-navigation-nav2-gazebo` you will use a real Nav2 navigation client to drive a robot through waypoints in Gazebo.
