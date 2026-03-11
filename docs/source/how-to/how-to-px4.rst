.. title:: How to Use PX4 with SMACC2
.. meta::
   :description: Complete guide for using the cl_px4_mr client library with SMACC2 for PX4 multirotor control — getting started, library tour, and usage patterns including writing custom behaviors and components.

How to Use PX4 with SMACC2
============================

Getting Started
----------------

Required Installations
~~~~~~~~~~~~~~~~~~~~~~~

**ROS 2 Jazzy**

.. code-block:: bash

   # Follow https://docs.ros.org/en/jazzy/Installation.html
   sudo apt install ros-jazzy-desktop

**PX4 Autopilot (SITL)**

.. code-block:: bash

   cd ~
   git clone https://github.com/PX4/PX4-Autopilot.git --recursive
   cd PX4-Autopilot
   bash Tools/setup/ubuntu.sh
   make px4_sitl gz_x500     # first build downloads models

**Micro XRCE-DDS Agent**

.. code-block:: bash

   sudo apt install ros-jazzy-micro-ros-agent
   # Or build from source:
   # git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
   # cd Micro-XRCE-DDS-Agent && mkdir build && cd build
   # cmake .. && make && sudo make install

**QGroundControl** (optional, for visualization)

.. code-block:: bash

   # Download from https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html
   chmod +x QGroundControl.AppImage
   ./QGroundControl.AppImage

Assembling the Workspace
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src

   # SMACC2 framework and client libraries
   git clone https://github.com/robosoft-ai/SMACC2.git -b jazzy

   # PX4 ROS 2 message definitions
   git clone https://github.com/PX4/px4_msgs.git -b release/1.15

The packages you need are:

- ``smacc2`` — core state machine framework
- ``smacc2_msgs`` — SMACC2 message definitions
- ``cl_px4_mr`` — PX4 multirotor client library (inside ``SMACC2/smacc2_client_library/``)
- ``sm_cl_px4_mr_test_1`` — reference state machine (inside ``SMACC2/smacc2_sm_reference_library/``)
- ``px4_msgs`` — PX4 ROS 2 message definitions

Building the Workspace
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd ~/ros2_ws
   source /opt/ros/jazzy/setup.bash
   colcon build --packages-select px4_msgs smacc2 smacc2_msgs cl_px4_mr sm_cl_px4_mr_test_1

.. note::

   You can also use ``colcon build --packages-up-to sm_cl_px4_mr_test_1``
   to build only the required dependency chain.

Launching the Application
~~~~~~~~~~~~~~~~~~~~~~~~~~

You need **four terminals**. Source the workspace in each:

.. code-block:: bash

   source ~/ros2_ws/install/setup.bash

**Terminal 1 — PX4 SITL Simulator**

.. code-block:: bash

   cd ~/PX4-Autopilot
   make px4_sitl gz_x500

**Terminal 2 — Micro XRCE-DDS Agent**

.. code-block:: bash

   MicroXRCEAgent udp4 -p 8888

**Terminal 3 — QGroundControl** (optional)

.. code-block:: bash

   ./QGroundControl.AppImage

**Terminal 4 — State Machine**

.. code-block:: bash

   source ~/ros2_ws/install/setup.bash
   ros2 launch sm_cl_px4_mr_test_1 sm_cl_px4_mr_test_1.py

The state machine executes this mission automatically:

.. code-block:: text

   Wait(5s) → Arm → Takeoff(5m) → GoTo(10,0,-5) → Orbit(3 loops) → Return(0,0,-5) → Land

Monitor with:

.. code-block:: bash

   # Current state
   ros2 topic echo /sm_cl_px4_mr_test_1/smacc/status

   # Transition log
   ros2 topic echo /sm_cl_px4_mr_test_1/smacc/transition_log

For a more complex workspace assembly example involving IsaacSim and NVIDIA
Isaac ROS, see the
`sm_nav2_test_7 README <https://github.com/robosoft-ai/nova_carter_sm_library/tree/jazzy/sm_nav2_test_7>`_.

Tour of the PX4 Client Behavior Library
-----------------------------------------

The ``cl_px4_mr`` client library provides SMACC2 integration for PX4
multirotor control via the XRCE-DDS bridge. It follows a pure
component-based architecture where the client orchestrates seven
specialized components and six flight behaviors.

For the full API reference, see the
`cl_px4_mr README <https://github.com/robosoft-ai/SMACC2/tree/jazzy/smacc2_client_library/cl_px4_mr>`_.

Folder Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

   cl_px4_mr/
   ├── include/cl_px4_mr/
   │   ├── cl_px4_mr.hpp                        # Client (orchestrator)
   │   ├── client_behaviors/
   │   │   ├── cb_arm_px4.hpp
   │   │   ├── cb_disarm_px4.hpp
   │   │   ├── cb_takeoff.hpp
   │   │   ├── cb_land.hpp
   │   │   ├── cb_go_to_location.hpp
   │   │   └── cb_orbit_location.hpp
   │   └── components/
   │       ├── cp_vehicle_command.hpp
   │       ├── cp_vehicle_status.hpp
   │       ├── cp_vehicle_local_position.hpp
   │       ├── cp_trajectory_setpoint.hpp
   │       ├── cp_offboard_keep_alive.hpp
   │       ├── cp_vehicle_command_ack.hpp
   │       └── cp_goal_checker.hpp
   ├── src/cl_px4_mr/
   │   ├── cl_px4_mr.cpp
   │   ├── client_behaviors/
   │   │   └── ... (matching .cpp files)
   │   └── components/
   │       └── ... (matching .cpp files)
   ├── CMakeLists.txt
   ├── package.xml
   └── README.md

Components
~~~~~~~~~~~

``ClPx4Mr`` is a **pure orchestrator client** — it contains zero business
logic and creates all seven components during initialization:

.. code-block:: c++

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

.. list-table::
   :header-rows: 1

   * - Component
     - Purpose
     - Key Methods / Signals
   * - ``CpVehicleCommand``
     - Publish vehicle commands
     - ``arm()``, ``forceArm()``, ``disarm()``, ``setOffboardMode()``, ``land()``, ``takeoff()``
   * - ``CpVehicleStatus``
     - Monitor vehicle state
     - ``isArmed()``, ``isLanded()``, ``getNavState()`` / Signals: ``onArmed_``, ``onDisarmed_``, ``onLanded_``
   * - ``CpVehicleLocalPosition``
     - Track position in NED frame
     - ``getX()``, ``getY()``, ``getZ()``, ``getHeading()`` / Signal: ``onPositionReceived_``
   * - ``CpTrajectorySetpoint``
     - Set target position (NED)
     - ``setPositionNED()``, ``hold()``, ``republishLast()``
   * - ``CpOffboardKeepAlive``
     - Offboard mode heartbeat (~20Hz)
     - ``enable()``, ``disable()``, ``isEnabled()``
   * - ``CpGoalChecker``
     - Detect goal achievement
     - ``setGoal()``, ``clearGoal()`` / Signal: ``onGoalReached_``
   * - ``CpVehicleCommandAck``
     - Receive command acknowledgments
     - ``getLastAckCommand()`` / Signal: ``onAckReceived_``

Behaviors
~~~~~~~~~~

All behaviors inherit from ``SmaccAsyncClientBehavior`` and post
``EvCbSuccess`` on completion or ``EvCbFailure`` on error.

.. list-table::
   :header-rows: 1

   * - Behavior
     - Constructor Parameters
     - Description
   * - ``CbArmPX4``
     - (none)
     - Arms the vehicle with retry logic (5 attempts, force-arm after 2)
   * - ``CbDisarmPX4``
     - (none)
     - Disarms the vehicle (3 retries)
   * - ``CbTakeOff``
     - ``targetAltitude`` (default 5.0m)
     - Enters offboard mode and climbs to altitude
   * - ``CbLand``
     - (none)
     - Disables offboard and sends land command
   * - ``CbGoToLocation``
     - ``targetX``, ``targetY``, ``targetZ``, optional ``yaw``
     - Flies to NED position, posts success when goal checker fires
   * - ``CbOrbitLocation``
     - ``centerX``, ``centerY``, ``altitude``, ``radius`` (5.0), ``angularVelocity`` (0.5), ``numOrbits`` (3)
     - Orbits a point using ``ISmaccUpdatable::update()``

Using the PX4 Client Behavior Library
---------------------------------------

Configuring the Orthogonal
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create an orthogonal that instantiates the ``ClPx4Mr`` client. All seven
components are created automatically:

.. code-block:: c++

   #include <cl_px4_mr/cl_px4_mr.hpp>

   class OrPx4 : public smacc2::Orthogonal<OrPx4>
   {
   public:
     void onInitialize() override
     {
       this->createClient<cl_px4_mr::ClPx4Mr>();
     }
   };

Register the orthogonal in your state machine's ``onInitialize()``:

.. code-block:: c++

   struct SmMyMission
     : smacc2::SmaccStateMachineBase<SmMyMission, MsDisarmedOnGround>
   {
     void onInitialize() override
     {
       this->createOrthogonal<OrPx4>();
     }
   };

Using a Behavior
~~~~~~~~~~~~~~~~~

Behaviors are configured in a state's ``staticConfigure()`` using
``configure_orthogonal<>``. Constructor parameters are passed as arguments.
The behavior executes asynchronously on state entry and posts events
(``EvCbSuccess``, ``EvCbFailure``) that drive transitions:

.. code-block:: c++

   #include <cl_px4_mr/client_behaviors/cb_go_to_location.hpp>

   struct StGoToWaypoint1 : smacc2::SmaccState<StGoToWaypoint1, MsInFlight>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvCbSuccess<CbGoToLocation, OrPx4>,
                  StOrbitLocation, SUCCESS>
     > reactions;

     static void staticConfigure()
     {
       // NED: 10m North, 0m East, 5m altitude (Z negative = up)
       configure_orthogonal<OrPx4, CbGoToLocation>(10.0f, 0.0f, -5.0f);
     }
   };

The pattern is the same for all PX4 behaviors — change the behavior class
and its parameters:

.. code-block:: c++

   // Arm the vehicle
   configure_orthogonal<OrPx4, CbArmPX4>();

   // Take off to 5 meters altitude
   configure_orthogonal<OrPx4, CbTakeOff>(5.0f);

   // Orbit: centerX, centerY, altitude, radius, angularVelocity, numOrbits
   configure_orthogonal<OrPx4, CbOrbitLocation>(10.0f, 0.0f, -5.0f, 5.0f, 0.5f, 3);

   // Land
   configure_orthogonal<OrPx4, CbLand>();

Writing Your Own Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a class that inherits from ``SmaccAsyncClientBehavior``, acquires
components via ``requiresComponent()``, connects to component signals, and
posts success or failure events when done.

**Header** (``include/cl_px4_mr/client_behaviors/cb_go_to_and_hold.hpp``):

.. code-block:: c++

   #pragma once

   #include <smacc2/smacc.hpp>

   namespace cl_px4_mr
   {

   class CpTrajectorySetpoint;
   class CpGoalChecker;

   class CbGoToAndHold : public smacc2::SmaccAsyncClientBehavior
   {
   public:
     CbGoToAndHold(float x, float y, float z, float holdSeconds);

     void onEntry() override;
     void onExit() override;

   private:
     void onGoalReached();

     float x_, y_, z_;
     float holdSeconds_;
     CpTrajectorySetpoint * trajectorySetpoint_ = nullptr;
     CpGoalChecker * goalChecker_ = nullptr;
   };

   }  // namespace cl_px4_mr

**Source** (``src/cl_px4_mr/client_behaviors/cb_go_to_and_hold.cpp``):

.. code-block:: c++

   #include <cl_px4_mr/client_behaviors/cb_go_to_and_hold.hpp>
   #include <cl_px4_mr/components/cp_goal_checker.hpp>
   #include <cl_px4_mr/components/cp_trajectory_setpoint.hpp>

   namespace cl_px4_mr
   {

   CbGoToAndHold::CbGoToAndHold(float x, float y, float z, float holdSeconds)
   : x_(x), y_(y), z_(z), holdSeconds_(holdSeconds)
   {
   }

   void CbGoToAndHold::onEntry()
   {
     // 1. Acquire components
     this->requiresComponent(trajectorySetpoint_);
     this->requiresComponent(goalChecker_);

     // 2. Connect to component signal
     this->getStateMachine()->createSignalConnection(
       goalChecker_->onGoalReached_,
       &CbGoToAndHold::onGoalReached, this);

     // 3. Command the vehicle
     trajectorySetpoint_->setPositionNED(x_, y_, z_);
     goalChecker_->setGoal(x_, y_, z_);
   }

   void CbGoToAndHold::onExit()
   {
     goalChecker_->clearGoal();
   }

   void CbGoToAndHold::onGoalReached()
   {
     RCLCPP_INFO(getLogger(),
       "CbGoToAndHold: goal reached, holding for %.1f seconds",
       holdSeconds_);
     std::this_thread::sleep_for(
       std::chrono::milliseconds(
         static_cast<int>(holdSeconds_ * 1000)));
     this->postSuccessEvent();
   }

   }  // namespace cl_px4_mr

The key steps for any custom behavior:

1. **Acquire components** with ``requiresComponent()`` in ``onEntry()``
2. **Connect to signals** with ``createSignalConnection()``
3. **Command the vehicle** through component methods
4. **Post events** (``postSuccessEvent()`` / ``postFailureEvent()``)
5. **Clean up** in ``onExit()``

If your behavior needs periodic updates (like ``CbOrbitLocation``), also
inherit from ``ISmaccUpdatable`` and override ``update()``.

Writing Your Own Component
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Components manage ROS 2 communication (publishers, subscribers, services)
and expose methods and signals for behaviors to use. Write a new component
when you need to:

- Subscribe to a PX4 topic not covered by existing components
- Publish to a new PX4 input topic
- Add reusable monitoring logic that multiple behaviors share

A component inherits from ``ISmaccComponent`` and optionally from
``ISmaccUpdatable`` for periodic updates.

**Header** (``include/cl_px4_mr/components/cp_vehicle_attitude.hpp``):

.. code-block:: c++

   #pragma once

   #include <smacc2/smacc.hpp>
   #include <px4_msgs/msg/vehicle_attitude.hpp>

   namespace cl_px4_mr
   {

   class CpVehicleAttitude : public smacc2::ISmaccComponent
   {
   public:
     CpVehicleAttitude();
     virtual ~CpVehicleAttitude();

     void onInitialize() override;

     float getRoll() const;
     float getPitch() const;
     float getYaw() const;

     smacc2::SmaccSignal<void()> onAttitudeReceived_;

   private:
     void onMessageReceived(const px4_msgs::msg::VehicleAttitude & msg);

     rclcpp::Subscription<px4_msgs::msg::VehicleAttitude>::SharedPtr sub_;
     float roll_ = 0.0f;
     float pitch_ = 0.0f;
     float yaw_ = 0.0f;
   };

   }  // namespace cl_px4_mr

**Source** (``src/cl_px4_mr/components/cp_vehicle_attitude.cpp``):

.. code-block:: c++

   #include <cl_px4_mr/components/cp_vehicle_attitude.hpp>

   namespace cl_px4_mr
   {

   CpVehicleAttitude::CpVehicleAttitude() {}
   CpVehicleAttitude::~CpVehicleAttitude() {}

   void CpVehicleAttitude::onInitialize()
   {
     auto node = this->getNode();

     sub_ = node->create_subscription<px4_msgs::msg::VehicleAttitude>(
       "/fmu/out/vehicle_attitude",
       rclcpp::SensorDataQoS(),
       std::bind(&CpVehicleAttitude::onMessageReceived, this,
                 std::placeholders::_1));

     RCLCPP_INFO(getLogger(),
       "CpVehicleAttitude: subscribed to /fmu/out/vehicle_attitude");
   }

   void CpVehicleAttitude::onMessageReceived(
     const px4_msgs::msg::VehicleAttitude & msg)
   {
     auto & q = msg.q;
     roll_ = std::atan2(2.0f * (q[0]*q[1] + q[2]*q[3]),
                        1.0f - 2.0f * (q[1]*q[1] + q[2]*q[2]));
     pitch_ = std::asin(2.0f * (q[0]*q[2] - q[3]*q[1]));
     yaw_ = std::atan2(2.0f * (q[0]*q[3] + q[1]*q[2]),
                       1.0f - 2.0f * (q[2]*q[2] + q[3]*q[3]));
     onAttitudeReceived_();
   }

   float CpVehicleAttitude::getRoll() const { return roll_; }
   float CpVehicleAttitude::getPitch() const { return pitch_; }
   float CpVehicleAttitude::getYaw() const { return yaw_; }

   }  // namespace cl_px4_mr

To include a new component in the client, add it to
``onComponentInitialization()``:

.. code-block:: c++

   this->createComponent<CpVehicleAttitude, TOrthogonal, TClient>();

If your component needs periodic computation, also inherit from
``ISmaccUpdatable`` and override ``update()``. See ``CpGoalChecker`` and
``CpOffboardKeepAlive`` for examples of this pattern.

**When to write a component vs. putting logic in a behavior:**

.. list-table::
   :header-rows: 1

   * - Criterion
     - Component
     - Behavior
   * - Lifetime
     - State machine scoped (lives as long as the client)
     - State scoped (created/destroyed with each state)
   * - Reusability
     - Shared across multiple behaviors
     - Single-purpose per state
   * - ROS 2 I/O
     - Owns publishers/subscribers
     - Uses components for I/O
   * - Signals
     - Emits signals for behaviors to connect to
     - Connects to component signals, posts state machine events
