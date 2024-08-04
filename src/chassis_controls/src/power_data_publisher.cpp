// Copyright 2016 Open Source Robotics Foundation, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#define Phoenix_No_WPI // remove WPI dependencies
#include "ctre/Phoenix.h"
#include "ctre/phoenix/unmanaged/Unmanaged.h"
#include "ctre/phoenix/cci/PDP_CCI.h"
#include <chrono>
#include <functional>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "general_interfaces/msg/power_data.hpp"

using namespace std::chrono_literals;
using namespace ctre::phoenix;
using namespace ctre::phoenix::platform;
using namespace ctre::phoenix::motorcontrol;
using namespace ctre::phoenix::motorcontrol::can;

/* This example creates a subclass of Node and uses std::bind() to register a
* member function as a callback from the timer. */

class PDPPublisher : public rclcpp::Node
{
public:
  PDPPublisher() : Node("pdp") {
    publisher_ = this->create_publisher<general_interfaces::msg::PowerData>("PowerData", 10);
    timer_ = this->create_wall_timer(1s, std::bind(&PDPPublisher::timer_callback, this));
  };

private:

  void timer_callback(){

    auto message = general_interfaces::msg::PowerData();

    int filled= 4;
    double currents [16] = {-1};
    double voltage;

    int err = (int)c_PDP_GetValues(0,&voltage,currents,5,&filled);
  
    if (!err){
      RCLCPP_INFO(get_logger(), "Updated PDP values.");
      message.filled = filled;
      message.voltage = voltage;
      for (unsigned i=0; i < message.currents.size(); i++){
        message.currents[i] = currents[i];
      }
    }
    else{
      RCLCPP_INFO(get_logger(), "Error updating PDP values.");
      message.filled = -1;
      message.voltage = -1;
      message.currents[0] = 69;
    }
    
    
    publisher_->publish(message);
  }
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Publisher<general_interfaces::msg::PowerData>::SharedPtr publisher_;
};

int main(int argc, char * argv[])
{
 rclcpp::init(argc, argv);
 rclcpp::spin(std::make_shared<PDPPublisher>());
 rclcpp::shutdown();
 return 0;
}
