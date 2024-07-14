
/*
What to test:
- can read from arduino? (send msg from arduino)
- can write to arduino? (send msg to arduino and view from arduinos end)
- check functionality of threadpoolexecutor
    - check number of threads running
- try using serial methods while my_serial_ is null
- stress test the system by sending multiple requests
*/


#include <gtest/gtest.h>
#include "include/serial_communication.hpp"
#include "third_party/SerialLibrary/include/serial/serial.h"

using namespace testing;


// Test fixture for SerialCommunication
class SerialCommsTest : public ::testing::Test {
protected:
    SerialCommunication* serialComm;

    void SetUp() override {
        serialComm = new SerialCommunication();
    }

    void TearDown() override {
        delete serialComm;
    }

    vector<string> messages_to_send = {"message 1;!", "message 2;!", "message 3;!", " message4;!", 
                                       "message 5;!", "message 6;!", "message 7;!", "message 8;!", 
                                       "message 9;!", "message 10;!"};
};

TEST_F(SerialCommsTest, ConnectSerialSuccessfully){
    serialComm->connect_serial(0);
    sleep(1);
    serialComm->isSerialPortOpen();

    ASSERT_FALSE(serialComm->get_connecting());
}

TEST_F(SerialCommsTest, ReadandWriteMessageSuccessfully){
    serialComm->connect_serial(0);
    serialComm->isSerialPortOpen();
    
    for (int i = 0; i < messages_to_send.size(); i++){
        serialComm->publishToArduino(messages_to_send[i]);
    } 

    ASSERT_FALSE(serialComm->get_connecting());

}



/*
//send in armPose format
TEST_F(SerialCommsTest, WriteMessageSuccessfully){
    string message_to_send = "testing!"; 

    serialComm->publishToArduino(message_to_send);

}

// receive in armPose format
TEST_F(SerialCommsTest, ReadMessageSuccessfully){
    string message_to_send = "sending_from_program!"; 
    serialComm->publishToArduino(message_to_send);

    string message_received = "se";

    ASSERT_EQ(message_to_send, message_received);
}

TEST_F(SerialCommsTest, ThreadPoolExecutorSuccessful){

}

//Execute multiple writes and try to get all the reads
TEST_F(SerialCommsTest, SerialStressTest){

}

TEST_F(SerialCommsTest, BlockCallsWhenSerialIsNull){


}
*/

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}



