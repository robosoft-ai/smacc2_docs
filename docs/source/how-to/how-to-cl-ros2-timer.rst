.. title:: How to Use cl_ros2_timer with SMACC2
.. meta::
   :description: Reference guide for the SMACC2 cl_ros2_timer client library — CbTimerCountdownOnce, CbTimerCountdownLoop, OrTimer setup, and chrono literal reference.

How to Use cl_ros2_timer with SMACC2
=====================================

``cl_ros2_timer`` provides timer-based orthogonal behaviors for SMACC2 state machines.
The ``OrTimer`` orthogonal holds a ``ClRos2Timer`` client; each behavior
(``CbTimerCountdownOnce``, ``CbTimerCountdownLoop``) creates its own dedicated wall timer
for accurate, period-independent firing.

Setting Up the Orthogonal
--------------------------

Define an ``OrTimer`` orthogonal in your state machine:

.. code-block:: c++

   // orthogonals/or_timer.hpp
   #include "cl_ros2_timer/cl_ros2_timer.hpp"
   #include "smacc2/smacc.hpp"

   class OrTimer : public smacc2::Orthogonal<OrTimer>
   {
   public:
     void onInitialize() override
     {
       this->createClient<cl_ros2_timer::ClRos2Timer>();
     }
   };

Register it in your state machine's ``onInitialize()``:

.. code-block:: c++

   void onInitialize() override
   {
     this->createOrthogonal<OrTimer>();
   }

CbTimerCountdownOnce
---------------------

**Header:** ``cl_ros2_timer/client_behaviors/cb_timer_countdown_once.hpp``

Posts ``EvTimer`` once after the specified duration, then stops. Use this to drive a timed
transition out of a state.

.. code-block:: c++

   // In state's staticConfigure():
   configure_orthogonal<OrTimer, CbTimerCountdownOnce>(5s);    // fire once after 5 seconds
   configure_orthogonal<OrTimer, CbTimerCountdownOnce>(4min);  // fire once after 4 minutes
   configure_orthogonal<OrTimer, CbTimerCountdownOnce>(500ms); // fire once after 500 ms

Full state example:

.. code-block:: c++

   struct StWaitForSensor : smacc2::SmaccState<StWaitForSensor, MyStateMachine>
   {
     using reactions = mpl::list<
       Transition<EvTimer<CbTimerCountdownOnce, OrTimer>, StNextState, SUCCESS>>;

     static void staticConfigure()
     {
       configure_orthogonal<OrTimer, CbTimerCountdownOnce>(10s);
     }
   };

CbTimerCountdownLoop
---------------------

**Header:** ``cl_ros2_timer/client_behaviors/cb_timer_countdown_loop.hpp``

Posts ``EvTimer`` repeatedly at the specified interval. Use this for periodic actions within
a state.

.. code-block:: c++

   configure_orthogonal<OrTimer, CbTimerCountdownLoop>(3s);    // fire every 3 seconds
   configure_orthogonal<OrTimer, CbTimerCountdownLoop>(500ms); // fire every 500 ms
   configure_orthogonal<OrTimer, CbTimerCountdownLoop>(1min);  // fire every minute

Chrono Literal Reference
-------------------------

Requires ``using namespace std::chrono_literals;`` — already in scope via rclcpp headers
in standard SMACC2 state files.

.. list-table::
   :header-rows: 1
   :widths: 15 25 20

   * - Literal
     - Meaning
     - Example
   * - ``ms``
     - milliseconds
     - ``500ms``
   * - ``s``
     - seconds
     - ``5s``
   * - ``min``
     - minutes
     - ``4min``
   * - ``h``
     - hours
     - ``2h``
