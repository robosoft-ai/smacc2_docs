Getting Started
=====

Naming Convention
------------

Because of the complexities of c++ template code and state machines in general, the Authors of the SMACC library developed a naming convention that users are strongly encouraged to follow.
Benefits of Adopting the Convention

The first benefit, is that the convention greatly improves code readability, especially from inside an IDE or the SMACC doxygen pages.

The second benefit, is that if you run into issues, the SMACC support team can quickly and easily get a handle on the broader picture of your problem.

And the third benefit, is that the SMACC development tools, such as the SMACC Viewer and the yet-to-be-built code-generator twill utilize this same naming convention and by adopting it, you ensure compatibility.
Prefixes

Header files have the following format…

- sm_ = state machine (ex: sm_dance_bot.h)
- ms_ = mode state (ex: ms_recover.h)
- ss_ = super state (ex: ss_sequence_1.h)
- st_ = state (ex: st_navigate_to_waypoints_x.h)
- sti_ = inner state (ex: sti_radial_rotate.h)
- sr_ = state reactor (ex: sr_all_events_go.h)
- or_ = orthogonal (ex: or_navigation.h)
- cl_ = client (ex: cl_move_base_z.h)
- cb_ = client behavior (ex: cb_timeout_watchdog.h) 

And then classes have the following format…

- Sm = state machine (ex: SmDanceBot)
- Ms = mode state (ex: MsRecover)
- Ss = super state (ex: SsSequence1.h)
- St = state (ex: StNavigateToWaypointsX)
- Sti = inner state (ex: StiRadialRotate)
- Sr = state reactor (ex: SrAllEventsGo)
- Or = orthogonal (ex: OrNavigation)
- Cl = client (ex: ClMoveBaseZ)
- Cb = client behavior (ex: CbTimeoutWatchdog) 

|
|

State Machine Folder Structure
------------

**Example State Machine Folder Structure**

sm_move_it…

    config
    docs
    include
        /sm_move_it
        /clients
    launch
    msg
    servers
        /fake_cube_perception_node
    simulation
        /models
        /robots
        /worlds
    src
        /clients
    test

sm_dance_bot…

    config
    docs
    include
    launch
    msg
        /action
    servers
        /action_server_node_3
            /include
            /src
        /led_action_server
        /lidar_node
        /service_node_3
        /temperature_sensor_node
    simulation
        /urdf
    src
    test

sm_atomic…

    config
    docs
    include
    launch
    msg
    src
    test

|
|

Client Library Folder Structure
------------

battery_monitor_client…

    include
    server
        /battery_monitor_node
            battery_monitor_nody.py
    src
    test
        /sm_clienttest_1
        /sm_clienttest_2


