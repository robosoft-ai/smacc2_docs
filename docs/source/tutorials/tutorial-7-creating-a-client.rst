.. title:: Tutorial 7 — Creating a Client
.. meta::
   :description: Build a SMACC2 ISmaccClient using the modern orchestrator pattern — zero business logic, pure component composition.

Tutorial 7 — Creating a Client
===============================

A SMACC2 client is a **state-machine-scoped object** that lives inside an orthogonal. In the modern, preferred pattern, a client is a **pure orchestrator** — it creates and composes components but contains no business logic of its own. In this tutorial you will study the ``ClPx4Mr`` client as a model for creating your own.

The Orchestrator Pattern
-------------------------

.. code-block:: c++

   // cl_px4_mr/cl_px4_mr.hpp
   #pragma once

   #include <smacc2/smacc.hpp>

   #include <cl_px4_mr/components/cp_goal_checker.hpp>
   #include <cl_px4_mr/components/cp_offboard_keep_alive.hpp>
   #include <cl_px4_mr/components/cp_trajectory_setpoint.hpp>
   #include <cl_px4_mr/components/cp_vehicle_command.hpp>
   #include <cl_px4_mr/components/cp_vehicle_command_ack.hpp>
   #include <cl_px4_mr/components/cp_vehicle_local_position.hpp>
   #include <cl_px4_mr/components/cp_vehicle_status.hpp>

   namespace cl_px4_mr
   {
   class ClPx4Mr : public smacc2::ISmaccClient
   {
   public:
     ClPx4Mr();
     virtual ~ClPx4Mr();

     template <typename TOrthogonal, typename TClient>
     void onComponentInitialization()
     {
       this->createComponent<CpVehicleCommand, TOrthogonal, TClient>();
       this->createComponent<CpTrajectorySetpoint, TOrthogonal, TClient>();
       this->createComponent<CpVehicleLocalPosition, TOrthogonal, TClient>();
       this->createComponent<CpOffboardKeepAlive, TOrthogonal, TClient>();
       this->createComponent<CpVehicleStatus, TOrthogonal, TClient>();
       this->createComponent<CpVehicleCommandAck, TOrthogonal, TClient>();
       this->createComponent<CpGoalChecker, TOrthogonal, TClient>();
     }
   };
   }  // namespace cl_px4_mr

That is the **entire client**. No business logic — just 7 ``createComponent<>()`` calls. Every piece of functionality lives in a component (see :doc:`tutorial-6-components`), and every action is performed by a behavior (see :doc:`tutorial-5-client-behaviors`).

``onComponentInitialization<TOrthogonal, TClient>()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This template method is called automatically by the framework when the client is created inside an orthogonal. The ``TOrthogonal`` and ``TClient`` type parameters are forwarded to each component so they can post correctly-typed events.

``createComponent<>()`` creates a component, calls its ``onInitialize()``, and registers it with the state machine.

|

Client Library Package Structure
---------------------------------

A client library is a ROS 2 package that builds into a shared library (``.so``):

.. code-block:: text

   cl_example/
   ├── include/cl_example/
   │   ├── cl_example.hpp                # Client header
   │   ├── client_behaviors/
   │   │   ├── cb_behavior_1.hpp         # Behavior headers
   │   │   └── cb_behavior_2.hpp
   │   └── components/
   │       ├── cp_component_1.hpp        # Component headers
   │       └── cp_component_2.hpp
   ├── src/cl_example/
   │   ├── cl_example.cpp                # Client implementation
   │   ├── client_behaviors/
   │   │   ├── cb_behavior_1.cpp         # Behavior implementations
   │   │   └── cb_behavior_2.cpp
   │   └── components/
   │       ├── cp_component_1.cpp        # Component implementations
   │       └── cp_component_2.cpp
   ├── CMakeLists.txt
   └── package.xml

All the ``.cpp`` files compile into a single ``.so`` shared library. State machines link against this library and include only the headers they need.

|

Contrast: Clients with Logic
------------------------------

Some older SMACC2 clients (like ``ClMoveit2z``) put business logic directly in the client:

.. code-block:: c++

   // cl_moveit2z/cl_moveit2z.hpp (older pattern)
   class ClMoveit2z : public smacc2::ISmaccClient
   {
   public:
     ClMoveit2z(std::string groupName);

     void onInitialize() override;

     std::shared_ptr<moveit::planning_interface::MoveGroupInterface>
       moveGroupClientInterface;
     std::shared_ptr<moveit::planning_interface::PlanningSceneInterface>
       planningSceneInterface;

     smacc2::SmaccSignal<void()> onSucceded_;
     smacc2::SmaccSignal<void()> onFailed_;

     void postEventMotionExecutionSucceded();
     void postEventMotionExecutionFailed();
   };

This pattern works but is less composable. The **orchestrator pattern** (``ClPx4Mr``) is preferred for new clients because:

- Components can be reused across different clients
- Components can be tested independently
- The client itself has no state to debug
- Adding functionality means adding a new component, not modifying the client

|

Creating Your Own Client
-------------------------

Follow these steps:

1. **Identify the components** you need (publishers, subscribers, monitors, etc.)
2. **Create each component** inheriting from ``ISmaccComponent`` (and optionally ``ISmaccUpdatable``)
3. **Create the client** inheriting from ``ISmaccClient`` with ``onComponentInitialization<>()``
4. **Create behaviors** inheriting from ``SmaccClientBehavior`` or ``SmaccAsyncClientBehavior``
5. **Create an orthogonal** that instantiates your client via ``createClient<>()``

The orthogonal is simple:

.. code-block:: c++

   class OrExample : public smacc2::Orthogonal<OrExample>
   {
   public:
     void onInitialize() override
     {
       this->createClient<ClExample>();
     }
   };

Then use behaviors in your states:

.. code-block:: c++

   static void staticConfigure()
   {
     configure_orthogonal<OrExample, CbBehavior1>(/* args */);
   }

|

Summary
-------

You learned:

- The **orchestrator pattern**: clients compose components, behaviors consume them
- ``onComponentInitialization<TOrthogonal, TClient>()`` creates all components with type context
- Client library package structure
- How to create a complete client from scratch

|

Next Steps
----------

In :doc:`tutorial-8-events-state-reactors` you will learn about custom events, typed events, and state reactors that combine multiple events into complex transition logic.
