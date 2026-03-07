.. title:: How to Debug with the SMACC RTA
.. meta::
   :description: Connect the SMACC2 Runtime Analyzer (RTA) to a running state machine for live visualization, and use ROS 2 CLI commands for manual debugging.

How to Debug with the SMACC RTA
=================================

The SMACC2 Runtime Analyzer (RTA) is a web-based tool that provides live visualization of a running state machine. This guide covers connecting the RTA and using ROS 2 topics for manual debugging.

SMACC RTA Viewer
-----------------

The RTA viewer is available at:

`robosoft.ai/viewer <https://robosoft.ai/viewer>`_

Connecting to a Running State Machine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Launch your state machine as usual (e.g., ``ros2 launch sm_atomic sm_atomic.py``).
2. Open the RTA viewer in your browser.
3. The viewer auto-detects SMACC2 state machines on the local ROS 2 network.

The viewer shows:

- **Current active state** — highlighted in the state diagram
- **State transition history** — timeline of all transitions with timestamps
- **Orthogonal status** — which behaviors are active on each orthogonal
- **Event flow** — which events triggered which transitions

|

ROS 2 Topic Debugging
-----------------------

Every SMACC2 state machine publishes status on standard topics. Replace ``[sm]`` with your state machine node name (e.g., ``sm_atomic``).

State Machine Status
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Current state machine status (state, orthogonals, behaviors)
   ros2 topic echo /[sm]/smacc/status

   # List all SMACC topics
   ros2 topic list | grep smacc

Transition History
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Watch state transitions in real time
   ros2 topic echo /[sm]/smacc/transition_log

Available Topics
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Topic
     - Message Type
     - Content
   * - ``/[sm]/smacc/status``
     - ``smacc2_msgs/msg/SmaccStatus``
     - Current state, orthogonals, behaviors
   * - ``/[sm]/smacc/transition_log``
     - ``smacc2_msgs/msg/SmaccTransitionLogEntry``
     - Transition history with timestamps

Node Inspection
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # List all nodes (find your state machine)
   ros2 node list

   # See all topics/services for your state machine node
   ros2 node info /[sm]

|

Common Debugging Techniques
-----------------------------

State Machine Not Starting
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Check that all required ROS 2 nodes are running (Nav2, PX4, etc.)
2. Verify topic availability: ``ros2 topic list``
3. Check logs: ``ros2 launch ... --screen`` to see all output

Stuck in a State
~~~~~~~~~~~~~~~~~

1. Check which behaviors are active: ``ros2 topic echo /[sm]/smacc/status``
2. For async behaviors, check if the expected event has been posted
3. Look for error messages in the terminal output
4. Verify the external system (Nav2 action server, PX4, etc.) is responding

Unexpected Transitions
~~~~~~~~~~~~~~~~~~~~~~~

1. Monitor the transition log: ``ros2 topic echo /[sm]/smacc/transition_log``
2. Check if multiple events are racing — the first matching event wins
3. Verify your transition table ``mpl::list`` order

|

Logging
--------

SMACC2 uses the ROS 2 logging framework. Increase verbosity for debugging:

.. code-block:: bash

   # Set log level for the state machine node
   ros2 run sm_atomic sm_atomic_node --ros-args --log-level debug
