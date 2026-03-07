.. title:: How to Use PX4 with SMACC2
.. meta::
   :description: Reference guide for using the cl_px4_mr client library with SMACC2 for PX4 multirotor control — components, behaviors, prerequisites, and example missions.

How to Use PX4 with SMACC2
============================

The ``cl_px4_mr`` client library integrates PX4 multirotor control with SMACC2 via the XRCE-DDS bridge. This guide covers the client, its 7 components, behaviors, and a complete example mission.

Getting Started
----------------

1. **PX4 Autopilot** with SITL (Software-In-The-Loop) simulation:

.. code-block:: bash

   cd ~/PX4-Autopilot
   make px4_sitl gz_x500

2. **Micro XRCE-DDS Agent** bridging PX4 ↔ ROS 2:

.. code-block:: bash

   MicroXRCEAgent udp4 -p 8888

3. **QGroundControl** (optional, for visualization):

.. code-block:: bash

   # Download from https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html
   ./QGroundControl.AppImage

4. **cl_px4_mr** and ``px4_msgs`` built in your colcon workspace

Overview
--------

``ClPx4Mr`` is a **pure orchestrator client** — it contains zero business logic and creates 7 components:

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

Components
----------

.. list-table::
   :header-rows: 1

   * - Component
     - Purpose
     - Key Methods/Signals
   * - ``CpVehicleCommand``
     - Publish vehicle commands
     - ``arm()``, ``forceArm()``, ``disarm()``, ``setOffboardMode()``, ``land()``, ``takeoff()``
   * - ``CpVehicleStatus``
     - Monitor vehicle status
     - ``isArmed()``, ``isLanded()``, ``getNavState()`` / Signals: ``onArmed_``, ``onDisarmed_``, ``onLanded_``
   * - ``CpVehicleLocalPosition``
     - Track vehicle position (NED)
     - ``getX()``, ``getY()``, ``getZ()``, ``getHeading()`` / Signal: ``onPositionReceived_``
   * - ``CpTrajectorySetpoint``
     - Set target position (NED)
     - ``setPositionNED()``, ``hold()``, ``republishLast()``
   * - ``CpOffboardKeepAlive``
     - Publish offboard control mode heartbeat
     - ``enable()``, ``disable()``, ``isEnabled()``
   * - ``CpGoalChecker``
     - Monitor goal achievement
     - ``setGoal()``, ``clearGoal()`` / Signal: ``onGoalReached_``
   * - ``CpVehicleCommandAck``
     - Receive command acknowledgments
     - ``getLastAckCommand()`` / Signal: ``onAckReceived_``

Behaviors
---------

.. list-table::
   :header-rows: 1

   * - Behavior
     - Type
     - Constructor Parameters
   * - ``CbArmPX4``
     - Async
     - (none) — retries up to 5 times
   * - ``CbDisarmPX4``
     - Async
     - (none) — retries up to 3 times
   * - ``CbTakeOff``
     - Async
     - ``targetAltitude`` (default 5.0m)
   * - ``CbLand``
     - Async
     - (none)
   * - ``CbGoToLocation``
     - Async
     - ``targetX``, ``targetY``, ``targetZ``, optional ``yaw``
   * - ``CbOrbitLocation``
     - Async + Updatable
     - ``centerX``, ``centerY``, ``altitude``, ``radius`` (5.0), ``angularVelocity`` (0.5), ``numOrbits`` (3)

All behaviors post ``EvCbSuccess`` on completion and ``EvCbFailure`` on error.

Orthogonal Setup
-----------------

.. code-block:: c++

   class OrPx4 : public smacc2::Orthogonal<OrPx4>
   {
   public:
     void onInitialize() override
     {
       this->createClient<cl_px4_mr::ClPx4Mr>();
     }
   };

Example Mission Flow
---------------------

From ``sm_cl_px4_mr_test_1`` — a complete flight mission:

.. code-block:: text

   MsDisarmedOnGround
     └── StWaitForReady ──[5s timer]──→ MsArmedOnGround
           └── StArmPx4 ──[success]──→ MsTakeoff
                 └── StTakeoff(5m) ──[success]──→ MsInFlight
                       ├── StGoToWaypoint1(10,0,-5) ──[success]──→
                       ├── StOrbitLocation(3 orbits) ──[success]──→
                       └── StReturnToBase(0,0,-5) ──[success]──→ MsLanding
                             └── StLand ──[success]──→ MsLanded

Example state:

.. code-block:: c++

   struct StGoToWaypoint1 : smacc2::SmaccState<StGoToWaypoint1, MsInFlight>
   {
     using SmaccState::SmaccState;

     typedef mpl::list<
       Transition<EvCbSuccess<CbGoToLocation, OrPx4>,
                  StOrbitLocation, SUCCESS>
       >reactions;

     static void staticConfigure()
     {
       // NED: 10m North, 0m East, 5m altitude (Z negative = up in NED)
       configure_orthogonal<OrPx4, CbGoToLocation>(10.0f, 0.0f, -5.0f);
     }
   };

Build and Run
--------------

.. code-block:: bash

   source /opt/ros/jazzy/setup.bash
   cd ~/ros2_ws
   colcon build --packages-select cl_px4_mr sm_cl_px4_mr_test_1
   source install/setup.bash

   # Terminal 1: PX4 SITL
   cd ~/PX4-Autopilot && make px4_sitl gz_x500

   # Terminal 2: XRCE-DDS Agent
   MicroXRCEAgent udp4 -p 8888

   # Terminal 3: State Machine
   ros2 launch sm_cl_px4_mr_test_1 sm_cl_px4_mr_test_1.py

NED Coordinate System
----------------------

PX4 uses the **NED** (North-East-Down) coordinate frame:

- **X** = North (positive forward)
- **Y** = East (positive right)
- **Z** = Down (negative values = altitude above ground)

So ``CbGoToLocation(10.0, 0.0, -5.0)`` means "fly 10m North at 5m altitude."
