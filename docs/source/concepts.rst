Concepts
=====

Intro to Substate Objects
------------

State Machines, are ultimately about the organization of code.

Let’s take a look at the taxonomy of SMACC objects inside of leaf state below, StAcquireSensors…


.. code-block:: console

   (.venv) $ pip install lumache


Let’s go through the objects one by one…

**Orthogonals:** Orthogonals are persistent for the life of the state machine. They can conceptually can be thought of as modular slots for the hardware devices that comprise a robot. Every Orthogonal should contain at least one client, and may contain multiple client behaviors. For more on orthogonals, click here.

**Clients:** Client objects are persistent for the life of the state machine. They are typically used to do things like, manage connections to outside nodes and devices, and contain code that we would want executed regardless of the current state. Clients are an important source of events.

**Client Behaviors:** Client behaviors are objects that are persistent for the life of the state. For this reason, they are used to execute state specific behaviors. In a given state, there can be multiple client behaviors in any orthogonal.

**State Reactors:** State Reactors are objects that receive events, and then generate one or more events. A good example of their use in practice, is the case of the state reactor, SrAllEventsGo. This State Reactor was created to deal with the following use case… A robot enters a state (in this case StAcquireSensors) where it wants to confirm that two different sensors have both been loaded and are working properly before moving onto the next state. So in this case, SrAllEventsGo needs to recieve two events, one from the temperature sensor orthogonal, and one from the lidar sensor, before the state reactor throws it’s own event, EvAllGo, which triggers the transition to next state.

**Events:** SMACC is an event-driven state machine library. As can be seen in the above example, events are created by Clients & Client Behaviors (although they can be created by States as well), then they are consumed by State Reactors & States. With the main difference being that State Reactors input events and output events, while states input events and output transitions.

Here is the code for the example image above…

.. code-block:: console

   #include <smacc/smacc.h>       
   namespace sm_dance_bot_strikes_back                     
   {       
   // STATE DECLARATION               
   struct StAcquireSensors : smacc::SmaccState<StAcquireSensors, MsDanceBotRunMode>                       
   {       
      using SmaccState::SmaccState;                                   
   // DECLARE CUSTOM OBJECT TAGS       
      struct ON_SENSORS_AVAILABLE : SUCCESS{};       
      struct SrAcquireSensors;       
   // TRANSITION TABLE       
      typedef mpl::list<       
      Transition<EvAllGo<SrAllEventsGo, SrAcquireSensors>, StEventCountDown, ON_SENSORS_AVAILABLE>, 
      Transition<EvActionSucceeded<CbAbsoluteRotate, OrNavigation>, StEventCountDown, SUCCESS>,   
      Transition<EvTimer<CbAbsoluteTimer, OrTimer>, StPreviousState, ABORT>               
      >reactions;       
   // STATE FUNCTIONS     
      static void staticConfigure()       
      {       
         configure_orthogonal<OrTemperatureSensor, CbConditionTemperatureSensor>();          
         configure_orthogonal<OrObstaclePerception, CbLidarSensor>();            
         configure_orthogonal<OrStringPublisher, CbStringPublisher>("Hello World!");          
         configure_orthogonal<OrNavigation, CbAbsoluteRotate>(360);       
         configure_orthogonal<OrTimer, CbAbsoluteTimer>(10);       
         // Create State Reactor        
         auto srAllSensorsReady = static_createStateReactor<SrAllEventsGo>();              
         srAllSensorsReady->addInputEvent<EvTopicMessage<CbLidarSensor, OrObstaclePerception>>();
         srAllSensorsReady->addInputEvent<EvTopicMessage<CbConditionTemperatureSensor, OrTemperatureSensor>>();                              
         srAllSensorsReady->setOutputEvent<EvAllGo<SrAllEventsGo, SrAcquireSensors>>();      
      }       
   };         
   } // namespace sm_dance_bot_strikes_back 

Creating recipes
----------------

To retrieve a list of random ingredients,
you can use the ``lumache.get_random_ingredients()`` function:

.. autofunction:: lumache.get_random_ingredients

The ``kind`` parameter should be either ``"meat"``, ``"fish"``,
or ``"veggies"``. Otherwise, :py:func:`lumache.get_random_ingredients`
will raise an exception.

.. autoexception:: lumache.InvalidKindError

For example:

>>> import lumache
>>> lumache.get_random_ingredients()
['shells', 'gorgonzola', 'parsley']

