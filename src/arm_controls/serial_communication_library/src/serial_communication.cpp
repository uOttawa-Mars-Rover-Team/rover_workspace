// USING ONLY ONE THREAD TO READ AND PUBLISH AND MAIN THREAD DOES THE REST

#include "serial_communication.hpp"
#include <thread>

SerialCommunication* SerialCommunication::instance = nullptr;

//============== Constructor ===============
SerialCommunication::SerialCommunication()
    : baudrate_(115200),
      port_("/dev/ttyACM0"),
      timeout_delay_(serial::Timeout::simpleTimeout(100)),
      startup_(true),
      connecting_(true),
      zeroing_(false),
      run_(true){
      //tp_executor(5) { // Initialize tp_executor with 5 workers

    RETRY_DELAY.it_value.tv_sec = 0.1; // Set delay to 0.1s
    RETRY_DELAY.it_value.tv_usec = 0;
    RETRY_DELAY.it_interval.tv_sec = 0;
    RETRY_DELAY.it_interval.tv_usec = 0;

    std::thread read_thread([this](){
        cout << "Read thread is running" << endl;
        read_serial();
    });
    read_thread.detach(); // read thread now runs independently

    instance = this; // Assign the instance pointer
    signal(SIGINT, signalHandler); // When Ctrl+C is pressed, run signalHandler (Destructor)
    signal(SIGALRM, signalHandler); // When SIGALRM triggers, run signalHandler (connect_serial)
    setitimer(ITIMER_REAL, &RETRY_DELAY, 0); // Once itimer expires, SIGALRM is triggered and connect_serial is run
}


//============== Destructor ==============
SerialCommunication::~SerialCommunication() {
    cout << "Destructor called" << endl;
    run_ = false;
    if (my_serial_ && my_serial_->isOpen()) {
        my_serial_->close();
    }
}


//============== Serial Communication Functions ==============
void SerialCommunication::connect_serial(int i) {
    try {
        connecting_ = true;
        cout << "Establishing serial connection..." << endl;

        setitimer(ITIMER_REAL, &RETRY_DELAY, 0);

        my_serial_ = make_unique<serial::Serial>(port_, baudrate_, timeout_delay_);

        if (my_serial_->isOpen()) {
            setitimer(ITIMER_REAL, 0, 0);
            cout << "Serial connection established." << endl;

            double delay = 0.0; // Default delay
            if (!startup_) {
                // If not starting up can immediately send a stop command
                // If the connecting is not starting up, this means the Arduino has been connected for a while
                delay = 0.001;
            } else {
                // If starting up, we must wait for the Arduino to fully boot up before sending a stop command
                delay = 1.0;
                startup_ = false;
            }
            sleep(delay);
            force_stop();
            
        } else {
            throw serial::PortNotOpenedException("Port failed to open.");
        }

    // Catching the different exceptions that can be thrown by the serial library
    } catch (const serial::PortNotOpenedException& e) {
        cerr << "Serial port could not be opened: " << e.what() << 
                    "\n trying every " << RETRY_DELAY.it_value.tv_sec << "s" << endl;
        connecting_ = true;
        connect_serial(i);
    } catch (const serial::IOException& e) {
        cerr << "I/O error while accessing serial port: " << e.what() << 
                    "\n trying every " << RETRY_DELAY.it_value.tv_sec << "s" << endl;
        connecting_ = true;
        connect_serial(i);
    } catch (const invalid_argument& e) {
        cerr << "Invalid argument provided to serial port: " << e.what() << 
                    "\n trying every " << RETRY_DELAY.it_value.tv_sec << "s" << endl;
        connecting_ = true;
        connect_serial(i); 
    } catch (const exception& e) {
        cerr << "General exception during connection: " << e.what() << 
                    "\n trying every " << RETRY_DELAY.it_value.tv_sec << "s" << endl;
        connecting_ = true;
        connect_serial(i); 
    }

}


void SerialCommunication::force_stop() {
    try {
        if (my_serial_) {
            setitimer(ITIMER_REAL, &RETRY_DELAY, 0);
            my_serial_->write("stop;!");
            setitimer(ITIMER_REAL, 0, 0);

            cout << "Movement message sent to serial: stop;!" << endl;
            connecting_ = false;
        }
    } catch (...) {
        cout << "Connection Error: serial failed, trying every " << RETRY_DELAY.it_value.tv_sec << "s" << endl;
        connecting_ = true;
        connect_serial(0);
    }
}


void SerialCommunication::read_serial() {
    sleep(1);
    cout << "Reading from serial port..." << endl;
    while (run_) {
        if (!connecting_ && my_serial_) {
            my_serial_->flushInput();
            string response = my_serial_->readline(65536, "!");
            //movement_ = response;  // save the message from serial
            if (!response.empty())
                publishMessage(response);
            
        }
    }
}


void SerialCommunication::write_serial() {
    cout << "Writing to serial port..." << endl;

    if (!connecting_ && !zeroing_ && my_serial_) {
        try {
            my_serial_->flushOutput();
            setitimer(ITIMER_REAL, &RETRY_DELAY, 0);
            my_serial_->write(movement_);
            cout << "Movement message to serial: " << movement_ << endl;
            setitimer(ITIMER_REAL, 0, 0);
        } catch (...) {
            setitimer(ITIMER_REAL, 0, 0);
            cout << "Connection Error: could not write serial" << endl;
            setitimer(ITIMER_REAL, &RETRY_DELAY, 0);
        }
    } else {
        setitimer(ITIMER_REAL, &RETRY_DELAY, 0);
    }
}


//============== Helper Functions ==============
void SerialCommunication::signalHandler(int signum) {
    // Ctrl+C signal
    if (signum == SIGINT) {
        if (instance) {
            instance->run_ = false;  // Signal the read thread to stop
            instance->~SerialCommunication();  // Explicitly call the destructor
        }
        exit(0);  // Exit the program

    // Timer is up signal
    } else if (signum == SIGALRM) {
        if (instance) {
            instance->connect_serial(signum);  // Handle SIGALRM
        }
    }
}


void SerialCommunication::publishToArduino(string message) {
    if (message != movement_) {
        movement_ = message;
        write_serial();
    }
}


string SerialCommunication::publishMessage(string message) {
    cout << "\nMessage read from serial: " << message << "\n";
        //"\n>>>>> threadId=" << tp_executor.getThreadId() << endl;
    return message;
}


void SerialCommunication::isSerialPortOpen() {
    if (my_serial_->isOpen()) {
        cout << "Serial port is open." << endl;
    } else {
        cout << "Serial port is not open." << endl;
    }
}

vector<string> SerialCommunication::get_arm_position(){
    // Checks if message starts with "f"
    if (movement_[0] == 'f') {
        vector<string> split_message = split_string(';', movement_);
        // Checks if message conatins all the arm info, ie "f;TW;SL;EL;PT;RL;EE"
        if (split_message.size() == 7) {
            return split_message;  // Should the returned string include the "f"?
        }
    }
    return {"E", "Movement contains invalid arm position"}; // change format of message?  
}

vector<string> SerialCommunication::split_string(char delimiter, string message) {
    vector<string> new_vector;
    stringstream ss(message);
    string token;
    while (getline(ss, token, delimiter)) {
        new_vector.push_back(token);
    }
    return new_vector;
}


/*
// USING THREADPOOLS

#include "serial_communication.hpp"

SerialCommunication* SerialCommunication::instance = nullptr;

//============== Constructor ===============
SerialCommunication::SerialCommunication()
    : baudrate_(115200),
      port_("/dev/ttyACM0"),
      timeout_delay_(serial::Timeout::simpleTimeout(100)),
      startup_(true),
      connecting_(true),
      zeroing_(false),
      run_(true),
      feedback_available_(false),
      tp_executor(5) { // Initialize tp_executor with 5 workers

    RETRY_DELAY.it_value.tv_sec = 0.1; // Set delay to 0.1s
    RETRY_DELAY.it_value.tv_usec = 0;
    RETRY_DELAY.it_interval.tv_sec = 0;
    RETRY_DELAY.it_interval.tv_usec = 0;

    tp_executor.enqueue([this]() {
        read_serial();
    });

    instance = this; // Assign the instance pointer
    signal(SIGINT, signalHandler);
    signal(SIGALRM, signalHandler); // When SIGALRM triggers, run signalHandler
    setitimer(ITIMER_REAL, &RETRY_DELAY, 0); // Once itimer expires, SIGALRM is triggered and connect_serial is run
}

//============== Destructor ==============
SerialCommunication::~SerialCommunication() {
    cout << "Destructor called" << endl;
    run_ = false;
    if (my_serial_ && my_serial_->isOpen()) {
        my_serial_->close();
    }
}


//============== Serial Communication Functions ==============
void SerialCommunication::connect_serial(int i) {
    try {
        connecting_ = true;
        cout << "Establishing serial connection..." << endl;

        setitimer(ITIMER_REAL, &RETRY_DELAY, 0);

        my_serial_ = make_unique<serial::Serial>(port_, baudrate_, timeout_delay_);

        if (my_serial_->isOpen()) {
            setitimer(ITIMER_REAL, 0, 0);
            cout << "Serial connection established." << endl;

            double delay = 0.0; // Default delay
            if (!startup_) {
                // If not starting up can immediately send a stop command
                // If the connecting is not starting up, this means the Arduino has been connected for a while
                delay = 0.001;
            } else {
                // If starting up, we must wait for the Arduino to fully boot up before sending a stop command
                delay = 1.0;
                startup_ = false;
            }
            sleep(delay);
            force_stop();
            
        } else {
            throw serial::PortNotOpenedException("Port failed to open.");
        }

    // Catching the different exceptions that can be thrown by the serial library
    } catch (const serial::PortNotOpenedException& e) {
        cerr << "Serial port could not be opened: " << e.what() << 
                    "\n trying every " << RETRY_DELAY.it_value.tv_sec << "s" << endl;
        connecting_ = true;
        connect_serial(i);
    } catch (const serial::IOException& e) {
        cerr << "I/O error while accessing serial port: " << e.what() << 
                    "\n trying every " << RETRY_DELAY.it_value.tv_sec << "s" << endl;
        connecting_ = true;
        connect_serial(i);
    } catch (const invalid_argument& e) {
        cerr << "Invalid argument provided to serial port: " << e.what() << 
                    "\n trying every " << RETRY_DELAY.it_value.tv_sec << "s" << endl;
        connecting_ = true;
        connect_serial(i); 
    } catch (const exception& e) {
        cerr << "General exception during connection: " << e.what() << 
                    "\n trying every " << RETRY_DELAY.it_value.tv_sec << "s" << endl;
        connecting_ = true;
        connect_serial(i); 
    }

}


void SerialCommunication::force_stop() {
    try {
        if (my_serial_) {
            setitimer(ITIMER_REAL, &RETRY_DELAY, 0);
            my_serial_->write("stop;!");
            setitimer(ITIMER_REAL, 0, 0);

            cout << "Movement message sent to serial: stop;!" << endl;
            connecting_ = false;
        }
    } catch (...) {
        cout << "Connection Error: serial failed, trying every " << RETRY_DELAY.it_value.tv_sec << "s" << endl;
        connecting_ = true;
        connect_serial(0);
    }
}


void SerialCommunication::read_serial() {
    sleep(1);
    cout << "Reading from serial port..." << endl;
    while (run_) {
        if (!connecting_ && my_serial_) {
            my_serial_->flushInput();
            string response = my_serial_->readline(65536, "!");
            movement_ = response;  // save the message from serial
            tp_executor.enqueue([this, response]() {
                publishMessage(response);
            });
        }
    }
}


void SerialCommunication::write_serial() {
    cout << "Writing to serial port..." << endl;

    if (!connecting_ && !zeroing_ && my_serial_) {
        try {
            my_serial_->flushOutput();
            setitimer(ITIMER_REAL, &RETRY_DELAY, 0);
            my_serial_->write(movement_);
            cout << "Movement message to serial: " << movement_ << endl;
            setitimer(ITIMER_REAL, 0, 0);
        } catch (...) {
            setitimer(ITIMER_REAL, 0, 0);
            cout << "Connection Error: could not write serial" << endl;
            setitimer(ITIMER_REAL, &RETRY_DELAY, 0);
        }
    } else {
        setitimer(ITIMER_REAL, &RETRY_DELAY, 0);
    }
}


//============== Helper Functions ==============
void SerialCommunication::signalHandler(int signum) {
    // Ctrl+C signal
    if (signum == SIGINT) {
        if (instance) {
            instance->run_ = false;  // Signal the read thread to stop
            instance->~SerialCommunication();  // Explicitly call the destructor
        }
        exit(0);  // Exit the program

    // Timer is up signal
    } else if (signum == SIGALRM) {
        if (instance) {
            instance->connect_serial(signum);  // Handle SIGALRM
        }
    }
}


void SerialCommunication::publishToArduino(string message) {
    if (message != movement_) {
        movement_ = message;
        write_serial();
    }
}


string SerialCommunication::publishMessage(string message) {
    cout << "\nMessage read from serial: " << message <<endl;
        //"\n>>>>> threadId=" << tp_executor.getThreadId() << endl;
    return message;
}


void SerialCommunication::isSerialPortOpen() {
    if (my_serial_->isOpen()) {
        cout << "Serial port is open." << endl;
    } else {
        cout << "Serial port is not open." << endl;
    }
}

vector<string> SerialCommunication::get_arm_position(){
    // Checks if message starts with "f"
    if (movement_[0] == 'f') {
        vector<string> split_message = split_string(';', movement_);
        // Checks if message conatins all the arm info, ie "f;TW;SL;EL;PT;RL;EE"
        if (split_message.size() == 7) {
            return split_message;  // Should the returns string include the "f"?
        }
    }
    return {"E", "Movement contains invalid arm position"}; // change format of message?  
}

vector<string> SerialCommunication::split_string(char delimiter, string message) {
    vector<string> new_vector;
    stringstream ss(message);
    string token;
    while (getline(ss, token, delimiter)) {
        new_vector.push_back(token);
    }
    return new_vector;
}
*/