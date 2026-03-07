.. title:: How to Use Core Client Behaviors
.. meta::
   :description: Reference for SMACC2 core client behaviors — CbSequence, CbSleepFor, CbCallService, CbWaitTopicMessage, CbRosLaunch, CbWaitNode, and more.

How to Use Core Client Behaviors
==================================

SMACC2 includes reusable client behaviors in ``smacc2/include/smacc2/client_behaviors/`` that work with **any** client library. This guide documents each one with header locations and usage.

CbSequence
----------

**Header:** ``smacc2/client_behaviors/cb_sequence.hpp``

Chains multiple behaviors to run sequentially within a single state. Each behavior starts after the previous one completes.

.. code-block:: c++

   #include <smacc2/client_behaviors/cb_sequence.hpp>

   static void staticConfigure()
   {
     auto sequence = configure_orthogonal<OrNavigation, CbSequence>();
     sequence->then<OrNavigation, CbNavigateGlobalPosition>(2.0, 0.0, 0.0);
     sequence->then<OrNavigation, CbRotate>(M_PI);
     sequence->then<OrNavigation, CbNavigateGlobalPosition>(0.0, 0.0, 0.0);
   }

The sequence posts ``EvCbSuccess`` when the last behavior in the chain completes.

CbSleepFor
-----------

**Header:** ``smacc2/client_behaviors/cb_sleep_for.hpp``

Async sleep for a specified duration, then posts success.

.. code-block:: c++

   #include <smacc2/client_behaviors/cb_sleep_for.hpp>

   static void staticConfigure()
   {
     configure_orthogonal<OrTimer, CbSleepFor>(rclcpp::Duration(5, 0));  // 5 seconds
   }

CbCallService
--------------

**Header:** ``smacc2/client_behaviors/cb_call_service.hpp``

Template class for calling a ROS 2 service. Posts success on response, failure on timeout.

.. code-block:: c++

   #include <smacc2/client_behaviors/cb_call_service.hpp>

   // Usage: CbServiceCall<ServiceType>
   static void staticConfigure()
   {
     auto cb = configure_orthogonal<OrService,
       CbServiceCall<std_srvs::srv::Trigger>>();
     // Configure the request before the state is entered
   }

Override ``onServiceResponse()`` for custom response handling:

.. code-block:: c++

   class CbMyServiceCall : public CbServiceCall<MyService>
   {
     void onServiceResponse(
       const typename MyService::Response::SharedPtr & response) override
     {
       // Handle response
     }
   };

CbWaitTopicMessage
-------------------

**Header:** ``smacc2/client_behaviors/cb_wait_topic_message.hpp``

Waits for the first message on a topic, with an optional guard predicate.

.. code-block:: c++

   #include <smacc2/client_behaviors/cb_wait_topic_message.hpp>

   static void staticConfigure()
   {
     // Wait for any message
     configure_orthogonal<OrSensor,
       CbWaitTopicMessage<sensor_msgs::msg::LaserScan>>("/scan");

     // Wait for a message matching a condition
     configure_orthogonal<OrSensor,
       CbWaitTopicMessage<sensor_msgs::msg::LaserScan>>(
         "/scan",
         [](const sensor_msgs::msg::LaserScan & msg) {
           return msg.ranges.size() > 0;
         });
   }

CbWaitTopic
------------

**Header:** ``smacc2/client_behaviors/cb_wait_topic.hpp``

Waits for a topic to appear in the ROS 2 graph. Posts success when the topic exists.

.. code-block:: c++

   #include <smacc2/client_behaviors/cb_wait_topic.hpp>

   static void staticConfigure()
   {
     configure_orthogonal<OrSensor, CbWaitTopic>("/scan");
   }

CbWaitActionServer
-------------------

**Header:** ``smacc2/client_behaviors/cb_wait_action_server.hpp``

Waits for an action server to become available, with a timeout.

.. code-block:: c++

   #include <smacc2/client_behaviors/cb_wait_action_server.hpp>

   static void staticConfigure()
   {
     configure_orthogonal<OrNavigation, CbWaitActionServer>(
       std::chrono::seconds(30));
   }

CbSubscriptionCallbackBase
----------------------------

**Header:** ``smacc2/client_behaviors/cb_subscription_callback_base.hpp``

Base class for subscription-driven behaviors. Override ``onMessageReceived()`` in your subclass.

.. code-block:: c++

   #include <smacc2/client_behaviors/cb_subscription_callback_base.hpp>

   class CbMySubscription
     : public CbSubscriptionCallbackBase<sensor_msgs::msg::LaserScan>
   {
     void onMessageReceived(const sensor_msgs::msg::LaserScan & msg) override
     {
       // Process each message
     }
   };

CbServiceServerCallbackBase
-----------------------------

**Header:** ``smacc2/client_behaviors/cb_service_server_callback_base.hpp``

Base class for service server behaviors. Override ``onServiceRequestReceived()`` in your subclass.

.. code-block:: c++

   #include <smacc2/client_behaviors/cb_service_server_callback_base.hpp>

   class CbMyServiceServer
     : public CbServiceServerCallbackBase<std_srvs::srv::Trigger>
   {
     void onServiceRequestReceived(
       const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
       std::shared_ptr<std_srvs::srv::Trigger::Response> response) override
     {
       response->success = true;
     }
   };

CbRosLaunch
------------

**Header:** ``smacc2/client_behaviors/cb_ros_launch.hpp``

Launches a ROS 2 package with configurable lifetime mode.

.. code-block:: c++

   #include <smacc2/client_behaviors/cb_ros_launch.hpp>

   static void staticConfigure()
   {
     // Detached: process outlives the behavior
     configure_orthogonal<OrLaunch, CbRosLaunch>(
       "my_package", "my_launch.py", RosLaunchMode::DETACHED);

     // Behavior-scoped: process stops when behavior exits
     configure_orthogonal<OrLaunch, CbRosLaunch>(
       "my_package", "my_launch.py", RosLaunchMode::CLIENT_BEHAVIOR_LIFETIME);
   }

CbWaitNode
-----------

**Header:** ``smacc2/client_behaviors/cb_wait_node.hpp``

Waits for a ROS 2 node to appear in the node graph. Posts success when found.

.. code-block:: c++

   #include <smacc2/client_behaviors/cb_wait_node.hpp>

   static void staticConfigure()
   {
     configure_orthogonal<OrSystem, CbWaitNode>("/my_node");
   }
