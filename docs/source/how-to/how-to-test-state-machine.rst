.. title:: How to Test a State Machine
.. meta::
   :description: Test SMACC2 state machines using unit test patterns, keyboard-driven manual testing, and ROS 2 topic verification.

How to Test a State Machine
=============================

SMACC2 state machines can be tested at multiple levels: automated unit tests, keyboard-driven manual testing, and ROS 2 topic-based verification. This guide covers patterns from the reference test state machines.

Unit Test State Machines
-------------------------

The SMACC2 reference library includes dedicated test state machines:

- ``sm_cl_ros2_timer_unit_test_1`` — tests timer client behaviors
- ``sm_cl_keyboard_unit_test_1`` — tests keyboard client behaviors

These are minimal state machines designed to exercise specific client library functionality.

Build and run a test state machine:

.. code-block:: bash

   colcon build --packages-select sm_cl_ros2_timer_unit_test_1
   source install/setup.bash
   ros2 launch sm_cl_ros2_timer_unit_test_1 sm_cl_ros2_timer_unit_test_1.py

The test state machine runs through its states automatically and logs results to the console.

Writing a Test State Machine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A test state machine follows the same structure as any SMACC2 state machine, but with states designed to verify specific behavior:

.. code-block:: c++

   struct StTestTimerCountdown : smacc2::SmaccState<StTestTimerCountdown, SmTest>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvTimer<CbTimerCountdownOnce, OrTimer>, StTestPass, SUCCESS>
       >reactions;

     static void staticConfigure()
     {
       configure_orthogonal<OrTimer, CbTimerCountdownOnce>(3);
     }

     void onEntry()
     {
       RCLCPP_INFO(getLogger(), "TEST: Timer countdown started, expecting 3 ticks");
     }
   };

   struct StTestPass : smacc2::SmaccState<StTestPass, SmTest>
   {
     using SmaccState::SmaccState;

     void onEntry()
     {
       RCLCPP_INFO(getLogger(), "TEST PASSED: Timer countdown completed");
     }
   };

Keyboard-Driven Manual Testing
--------------------------------

The ``cl_keyboard`` client provides interactive manual control. Use it for exploratory testing:

.. code-block:: c++

   // In your state machine's onInitialize()
   this->createOrthogonal<OrKeyboard>();

   // In state transition tables
   Transition<EvKeyPressN<CbDefaultKeyboardBehavior, OrKeyboard>,
              StNextState, NEXT>

With keyboard navigation you can:

- Step through states manually (N = next, P = previous)
- Trigger specific events (A, B, C keys in ``sm_three_some``)
- Test error recovery by pressing keys that trigger failure transitions

Verifying Transitions via ROS 2 Topics
----------------------------------------

Monitor state machine behavior programmatically using ROS 2 topics:

.. code-block:: bash

   # Watch state transitions
   ros2 topic echo /[sm]/smacc/transition_log

   # Check current state
   ros2 topic echo /[sm]/smacc/status --once

   # Record transitions for later analysis
   ros2 bag record /[sm]/smacc/status /[sm]/smacc/transition_log

You can also write a ROS 2 test node that subscribes to the state machine status topic and asserts expected state sequences:

.. code-block:: python

   import rclpy
   from rclpy.node import Node
   from smacc2_msgs.msg import SmaccStatus

   class SmaccTestNode(Node):
       def __init__(self):
           super().__init__('smacc_test')
           self.states_visited = []
           self.sub = self.create_subscription(
               SmaccStatus, '/sm_test/smacc/status',
               self.status_callback, 10)

       def status_callback(self, msg):
           self.states_visited.append(msg.current_state_name)
           self.get_logger().info(f'State: {msg.current_state_name}')

Testing Checklist
------------------

When testing a state machine:

1. **Build with warnings enabled**: ``colcon build --packages-select my_sm --cmake-args -DCMAKE_CXX_FLAGS="-Wall -Wextra"``
2. **Run through the happy path**: verify all expected state transitions occur
3. **Test error paths**: trigger failure conditions and verify recovery transitions
4. **Monitor with RTA**: use the RTA viewer to visually confirm state flow
5. **Check for resource leaks**: watch ``ros2 node list`` and ``ros2 topic list`` for stale resources
6. **Test with keyboard**: use manual keyboard navigation to step through edge cases
7. **Record bags**: record state machine topics for regression testing
