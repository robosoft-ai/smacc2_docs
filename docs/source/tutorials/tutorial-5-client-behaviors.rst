.. title:: Tutorial 5 — Client Behaviors
.. meta::
   :description: Learn to write synchronous and asynchronous SMACC2 client behaviors, including the lifecycle methods, event posting, and the core behavior catalog.

Tutorial 5 — Client Behaviors
==============================

Client behaviors are the **workhorses** of a SMACC2 state machine. They execute actions, monitor conditions, and post events that drive state transitions. In this tutorial you will learn the difference between synchronous and asynchronous behaviors, study the ``CbArmPX4`` behavior as a real-world example, and discover the core behavior catalog.

Sync vs Async
-------------

SMACC2 provides two base classes for behaviors:

.. list-table::
   :header-rows: 1

   * - Base Class
     - Execution Model
     - Use When
   * - ``SmaccClientBehavior``
     - Synchronous — ``onEntry()`` runs on the state machine thread and must return quickly
     - Short operations (configure a parameter, subscribe to a topic)
   * - ``SmaccAsyncClientBehavior``
     - Asynchronous — ``onEntry()`` runs in its own thread
     - Long-running operations (wait for a condition, navigate, retry loops)

Behavior Lifecycle
------------------

Every behavior goes through this sequence when its owning state is entered:

1. **``runtimeConfigure()``** — called before ``onEntry()``, on the state machine thread. Use it to fetch components or configure parameters.
2. **``onEntry()``** — the main execution body. For async behaviors, this runs in a dedicated thread.
3. **``onExit()``** — called when the state is exited. Use it for cleanup.

Async behaviors have additional capabilities:

- **``postSuccessEvent()``** — posts ``EvCbSuccess`` to trigger a ``SUCCESS`` transition
- **``postFailureEvent()``** — posts ``EvCbFailure`` to trigger an ``ABORT`` transition
- **``isShutdownRequested()``** — check this periodically in long loops to honor shutdown requests

Accessing Components
--------------------

Behaviors access components from their client via ``requiresComponent()``:

.. code-block:: c++

   CpVehicleCommand * vehicleCommand_ = nullptr;
   CpVehicleStatus * vehicleStatus_ = nullptr;

   void onEntry() override
   {
     this->requiresComponent(vehicleCommand_);
     this->requiresComponent(vehicleStatus_);
     // Now vehicleCommand_ and vehicleStatus_ point to live components
   }

Example: CbArmPX4 (Async Behavior)
------------------------------------

The ``CbArmPX4`` behavior from the ``cl_px4_mr`` client library is a complete async behavior example. Here is the header:

.. code-block:: c++

   // cl_px4_mr/client_behaviors/cb_arm_px4.hpp
   #pragma once

   #include <atomic>
   #include <smacc2/smacc.hpp>

   namespace cl_px4_mr
   {
   class CpVehicleCommand;
   class CpVehicleStatus;

   class CbArmPX4 : public smacc2::SmaccAsyncClientBehavior
   {
   public:
     CbArmPX4();

     void onEntry() override;
     void onExit() override;

   private:
     void onArmedCallback();

     CpVehicleCommand * vehicleCommand_ = nullptr;
     CpVehicleStatus * vehicleStatus_ = nullptr;
     std::atomic<bool> armed_{false};
     static constexpr int MAX_RETRIES = 5;
     static constexpr int RETRY_INTERVAL_SEC = 5;
   };
   }  // namespace cl_px4_mr

And the implementation:

.. code-block:: c++

   // cl_px4_mr/client_behaviors/cb_arm_px4.cpp
   #include <cl_px4_mr/client_behaviors/cb_arm_px4.hpp>
   #include <cl_px4_mr/components/cp_vehicle_command.hpp>
   #include <cl_px4_mr/components/cp_vehicle_status.hpp>

   namespace cl_px4_mr
   {
   CbArmPX4::CbArmPX4() {}

   void CbArmPX4::onEntry()
   {
     this->requiresComponent(vehicleCommand_);
     this->requiresComponent(vehicleStatus_);

     this->getStateMachine()->createSignalConnection(
       vehicleStatus_->onArmed_, &CbArmPX4::onArmedCallback, this);

     for (int attempt = 0; attempt < MAX_RETRIES; attempt++)
     {
       if (attempt < 2)
       {
         RCLCPP_INFO(
           getLogger(), "CbArmPX4: sending arm command (attempt %d/%d)",
           attempt + 1, MAX_RETRIES);
         vehicleCommand_->arm();
       }
       else
       {
         RCLCPP_WARN(
           getLogger(), "CbArmPX4: force-arming (attempt %d/%d)",
           attempt + 1, MAX_RETRIES);
         vehicleCommand_->forceArm();
       }

       for (int i = 0; i < RETRY_INTERVAL_SEC * 10; i++)
       {
         if (armed_) break;
         std::this_thread::sleep_for(std::chrono::milliseconds(100));
       }

       if (armed_)
       {
         RCLCPP_INFO(getLogger(), "CbArmPX4: vehicle ARMED - posting success");
         this->postSuccessEvent();
         return;
       }

       RCLCPP_WARN(
         getLogger(), "CbArmPX4: attempt %d/%d timed out, retrying...",
         attempt + 1, MAX_RETRIES);
     }

     RCLCPP_ERROR(
       getLogger(), "CbArmPX4: all %d attempts failed - posting failure",
       MAX_RETRIES);
     this->postFailureEvent();
   }

   void CbArmPX4::onExit() {}

   void CbArmPX4::onArmedCallback() { armed_ = true; }
   }  // namespace cl_px4_mr

Key patterns in this behavior:

1. **``requiresComponent()``** — gets pointers to ``CpVehicleCommand`` and ``CpVehicleStatus``
2. **``createSignalConnection()``** — connects the ``onArmed_`` signal from ``CpVehicleStatus`` to a local callback. The connection is automatically cleaned up on state exit.
3. **Retry loop** — because this is async, the loop runs in its own thread and doesn't block the state machine.
4. **``postSuccessEvent()`` / ``postFailureEvent()``** — posts ``EvCbSuccess`` or ``EvCbFailure`` to drive the transition.

Default Events
--------------

Every behavior automatically has these events available:

- ``EvCbSuccess<BehaviorType, OrthogonalType>`` — posted by ``postSuccessEvent()``
- ``EvCbFailure<BehaviorType, OrthogonalType>`` — posted by ``postFailureEvent()``
- ``EvCbFinished<BehaviorType, OrthogonalType>`` — posted when ``onEntry()`` returns (async only)

Use them in transition tables:

.. code-block:: c++

   typedef mpl::list<
     Transition<EvCbSuccess<CbArmPX4, OrPx4>, StTakeoff, SUCCESS>,
     Transition<EvCbFailure<CbArmPX4, OrPx4>, StError, ABORT>
     >reactions;

Core Client Behaviors Catalog
------------------------------

SMACC2 ships with reusable behaviors that work with any client:

.. list-table::
   :header-rows: 1

   * - Behavior
     - Type
     - Purpose
   * - ``CbSleepFor``
     - Async
     - Sleep for a ``rclcpp::Duration``, then post success
   * - ``CbWaitTopic``
     - Async
     - Wait until a ROS 2 topic exists
   * - ``CbWaitTopicMessage``
     - Async
     - Wait for the first message on a topic (with optional guard predicate)
   * - ``CbWaitActionServer``
     - Async
     - Wait for an action server to become available
   * - ``CbCallService``
     - Async
     - Call a ROS 2 service and post success/failure
   * - ``CbSequence``
     - Async
     - Chain multiple behaviors to run in sequence within one state
   * - ``CbRosLaunch``
     - Async
     - Launch a ROS 2 package (detached or behavior-scoped)
   * - ``CbWaitNode``
     - Async
     - Wait for a ROS 2 node to appear

These are located in ``smacc2/include/smacc2/client_behaviors/``. See the :doc:`/how-to/how-to-core-client-behaviors` guide for usage details.

Summary
-------

You learned:

- The difference between sync (``SmaccClientBehavior``) and async (``SmaccAsyncClientBehavior``) behaviors
- The behavior lifecycle: ``runtimeConfigure()`` → ``onEntry()`` → ``onExit()``
- How to access components with ``requiresComponent()``
- How to connect to signals with ``createSignalConnection()``
- How to post success/failure events from async behaviors
- The core behavior catalog

Next Steps
----------

In :doc:`tutorial-6-components` you will learn how to create reusable components that provide data and signals to behaviors.
