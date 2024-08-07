#ifndef SERIAL_COMMUNICATION_HPP
#define SERIAL_COMMUNICATION_HPP

#include <iostream>
#include <string>
#include <csignal>
#include <sys/time.h>
#include <signal.h>
#include <unistd.h>
#include <vector>
#include <sstream>

//#include "rclcpp/rclcpp.hpp"

#include "../third_party/SerialLibrary/include/serial/serial.h"
#include "../third_party/ThreadPool/ThreadPool.h"

using namespace std;

/**
 * @brief SerialCommunication class
 * 
 * This class is responsible for establishing a serial connection with the Arduino and sending and receiving messages
 * from the Arduino. 
 * 
 * NOTE: To send a message to the arduino, use the publishToArduino(string message) function
 */

class SerialCommunication {
private:
    // Arduino Parameters
    const int baudrate_;
    const string port_;
    const serial::Timeout timeout_delay_;
    unique_ptr<serial::Serial> my_serial_; // Serial object to establish connection

    bool startup_;
    bool connecting_;
    bool zeroing_;
    bool run_; // Threads stop running if false
    bool feedback_available_;
    string movement_;
    string latest_position_;
    string latest_peripherals_;

    // Threading
    //ThreadPool tp_executor;

    // Timer and Signals
    struct itimerval RETRY_DELAY;

    // To display current time in print statements
    struct timespec current_time_;

    static SerialCommunication* instance; // Pointer to the instance of the class

public:
    SerialCommunication();
    ~SerialCommunication();

    // Serial Communication Methods

    /**
     * @brief Connects to the serial port
     * @param i The signal number
     * @return None
     * 
     * This function will attempt to connect to the serial port and will retry every 0.1s if it fails
     */
    void connect_serial(int i);

    /**
     * @brief Sends a stop command to the Arduino to stop movement
     * @return None
     */
    void force_stop();

    /**
     * @brief Reads from the serial port
     * @return None
     *
     * This function will read from the serial port and send a child thread to return the 
     * message read using thread pool executor
     */
    void read_serial();

    /**
     * @brief Writes a message to the serial port
     * @return None
     */
    void write_serial();


    // Helper Methods
    /**
     * @brief Signal handler for the timer
     * @param signum The signal number
     * @return None
     */
    static void signalHandler(int signum);

    /**
     * @brief Publishes a message to the Arduino
     * @param message The message to publish
     * 
     * This function will only write to the arduino if it is different from the last message sent
     * Use this method if you want to write to the arduino
     */
    void publishToArduino(string message);

    /**
     * @brief Publishes a message to the Arduino
     * @param message The message to publish
     * @return string The message that was published
     */
    string publishMessage(string message);

    /**
     * @brief Checks if the serial port is open and prints respective message
     * @return None
     */
    void isSerialPortOpen();

    /**
     * @brief Gets the current arm position
     * @return vector<string> A vector of strings representing the arm position, ie ["f", "TW", "SL", "EL", "PT", "RL", "EE]
     */
    vector<string> get_arm_position();

    /**
     * @brief Gets the latest position of the arm
     * @return string Instance variable with the latest position of the arm
     */
    string get_latest_position();

    /**
     * @brief Gets the latest peripherals of the arm
     * @return string Instance variable with the latest peripherals of the arm
     */
    string get_peripheral_feedback();

    /**
     * @brief Splits a string into a vector of strings based on a delimiter
     * @param delimiter The character to split the string on
     * @param message The string to split
     * @return vector<string> A vector of strings split by the delimiter
     */
    vector<string> split_string(char delimiter, string message);

    // This method is used for testing purposes
    // Returns connection status of the serial port
    bool get_connecting() { return connecting_; }
};

#endif // SERIAL_COMMUNICATION_HPP