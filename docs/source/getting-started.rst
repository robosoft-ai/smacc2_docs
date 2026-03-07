.. title:: Getting Started
.. meta::
   :description: Installation and setup instructions for getting started with the SMACC2 state machine library for ROS2.

Getting Started
===============

Install ROS 2
--------------

SMACC2 targets **ROS 2 Jazzy** on Ubuntu 24.04. Follow the official installation guide:

- `ROS 2 Jazzy Installation <https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html>`_

After installing, source the setup file:

.. code-block:: bash

   source /opt/ros/jazzy/setup.bash

|

Install SMACC2
----------------

Create a ROS 2 workspace:

.. code-block:: bash

   mkdir -p ~/ros2_ws/src

Clone the SMACC2 repository:

.. code-block:: bash

   cd ~/ros2_ws/src
   git clone https://github.com/robosoft-ai/SMACC2.git

Install dependencies:

.. code-block:: bash

   cd ~/ros2_ws
   rosdep install --from-paths src --ignore-src -r -y

Build:

.. code-block:: bash

   colcon build

Source the workspace after the build completes:

.. code-block:: bash

   source ~/ros2_ws/install/setup.bash

|

Download the SMACC Viewer (RTA)
---------------------------------

The SMACC Runtime Analyzer (RTA) is a graphical tool for real-time visualization and debugging of SMACC2 state machines. Download and install instructions are available at:

- `SMACC Viewer Installation <https://robosoft.ai/viewer>`_

For naming conventions, folder structures, and other foundational concepts, see :doc:`concepts/basics`.

