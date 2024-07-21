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
    
    for (size_t i = 0; i < messages_to_send.size(); i++){
        serialComm->publishToArduino(messages_to_send[i]);
    } 

    ASSERT_FALSE(serialComm->get_connecting());

}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}



