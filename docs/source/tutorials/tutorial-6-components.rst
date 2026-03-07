.. title:: Tutorial 6 — Components
.. meta::
   :description: Create SMACC2 ISmaccComponent objects — subscriber-based data stores and updatable monitors — with signals for decoupled communication.

Tutorial 6 — Components
========================

Components are **state-machine-scoped objects** that provide reusable functionality to behaviors. They live inside a client and survive state transitions. In this tutorial you will study two component patterns from the ``cl_px4_mr`` client library: a **subscriber data store** and an **updatable monitor**.

ISmaccComponent Basics
-----------------------

All components inherit from ``smacc2::ISmaccComponent``:

.. code-block:: c++

   class MyComponent : public smacc2::ISmaccComponent
   {
   public:
     void onInitialize() override
     {
       // Called when the component is created by the client
       // Set up subscriptions, publishers, other components
     }
   };

Key rules:

- ``onInitialize()`` is called after all components are created — you can safely call ``requiresComponent()`` here to get sibling components.
- Components live as long as the state machine. They are not destroyed on state transitions.
- Components expose ``SmaccSignal`` members for behaviors to connect to.

|

Pattern 1: Subscriber + Data Store
------------------------------------

``CpVehicleLocalPosition`` subscribes to a PX4 topic, stores the latest position data behind a mutex, and fires a signal when new data arrives.

.. code-block:: c++

   // cl_px4_mr/components/cp_vehicle_local_position.hpp
   #pragma once

   #include <mutex>
   #include <px4_msgs/msg/vehicle_local_position.hpp>
   #include <rclcpp/rclcpp.hpp>
   #include <smacc2/smacc.hpp>

   namespace cl_px4_mr
   {
   class CpVehicleLocalPosition : public smacc2::ISmaccComponent
   {
   public:
     CpVehicleLocalPosition();
     virtual ~CpVehicleLocalPosition();

     void onInitialize() override;

     float getX() const;
     float getY() const;
     float getZ() const;
     float getHeading() const;
     bool isValid() const;

     smacc2::SmaccSignal<void()> onPositionReceived_;

   private:
     void onPositionMessage(
       const px4_msgs::msg::VehicleLocalPosition::SharedPtr msg);

     rclcpp::Subscription<px4_msgs::msg::VehicleLocalPosition>::SharedPtr
       subscriber_;
     float x_ = 0.0f;
     float y_ = 0.0f;
     float z_ = 0.0f;
     float heading_ = 0.0f;
     bool valid_ = false;
     mutable std::mutex mutex_;
   };
   }  // namespace cl_px4_mr

Key elements:

- **ROS subscription** — created in ``onInitialize()`` using the state machine's node handle
- **Mutex-protected data** — getter methods lock the mutex for thread-safe reads
- **SmaccSignal** — ``onPositionReceived_`` fires in the subscription callback so behaviors can react to position updates
- **Thread safety** — the subscription callback runs on a ROS executor thread, so all shared data is mutex-protected

|

Pattern 2: Updatable Monitor
------------------------------

``CpGoalChecker`` inherits from both ``ISmaccComponent`` and ``ISmaccUpdatable``, which gives it a periodic ``update()`` method called at ~20 Hz by the SignalDetector.

.. code-block:: c++

   // cl_px4_mr/components/cp_goal_checker.hpp
   #pragma once

   #include <cmath>
   #include <smacc2/smacc.hpp>

   namespace cl_px4_mr
   {
   class CpVehicleLocalPosition;

   class CpGoalChecker : public smacc2::ISmaccComponent,
                          public smacc2::ISmaccUpdatable
   {
   public:
     CpGoalChecker();
     virtual ~CpGoalChecker();

     void onInitialize() override;
     void update() override;

     void setGoal(float x, float y, float z,
                  float xy_tolerance = 0.5f, float z_tolerance = 0.3f);
     void clearGoal();
     bool isGoalActive() const;

     smacc2::SmaccSignal<void()> onGoalReached_;

   private:
     CpVehicleLocalPosition * localPosition_ = nullptr;
     float goalX_ = 0.0f;
     float goalY_ = 0.0f;
     float goalZ_ = 0.0f;
     float xyTolerance_ = 0.5f;
     float zTolerance_ = 0.3f;
     bool goalActive_ = false;
   };
   }  // namespace cl_px4_mr

Key elements:

- **``ISmaccUpdatable``** — the ``update()`` method is called periodically by the SMACC2 SignalDetector
- **``requiresComponent()``** — in ``onInitialize()``, it gets a pointer to ``CpVehicleLocalPosition`` (a sibling component on the same client)
- **Goal checking** — ``update()`` reads the current position from ``CpVehicleLocalPosition``, compares it against the goal, and fires ``onGoalReached_`` when within tolerance
- **Signal** — behaviors like ``CbTakeOff`` and ``CbGoToLocation`` connect to ``onGoalReached_`` to know when to post success

|

Component-to-Component Dependencies
-------------------------------------

Components can depend on sibling components within the same client:

.. code-block:: c++

   void CpGoalChecker::onInitialize()
   {
     requiresComponent(localPosition_);  // Gets CpVehicleLocalPosition
   }

This is safe because ``onInitialize()`` is called after all components are created by the client's ``onComponentInitialization()``.

|

SmaccSignal: Declaring and Connecting
--------------------------------------

Declare a signal in a component:

.. code-block:: c++

   // In component header
   smacc2::SmaccSignal<void()> onGoalReached_;

Fire the signal:

.. code-block:: c++

   // In component implementation
   onGoalReached_();

Connect to the signal from a behavior:

.. code-block:: c++

   // In behavior's onEntry()
   this->getStateMachine()->createSignalConnection(
     goalChecker_->onGoalReached_, &CbTakeOff::onGoalReachedCallback, this);

Always use ``createSignalConnection()`` instead of raw ``boost::signals2::connect()``. The framework manages connection lifetimes and automatically disconnects when state-scoped objects (like behaviors) are destroyed on state exit.

|

Summary
-------

You learned:

- ``ISmaccComponent`` provides the ``onInitialize()`` lifecycle hook
- The subscriber + data store pattern: ROS subscription → mutex-protected data → ``SmaccSignal``
- The updatable monitor pattern: ``ISmaccUpdatable`` for periodic checking → ``SmaccSignal``
- Component-to-component dependencies via ``requiresComponent()``
- Signal declaration, firing, and safe connection via ``createSignalConnection()``

|

Next Steps
----------

In :doc:`tutorial-7-creating-a-client` you will create a complete client that composes components using the orchestrator pattern.
