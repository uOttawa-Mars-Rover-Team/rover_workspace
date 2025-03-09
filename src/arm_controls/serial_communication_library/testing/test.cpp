#include <gtest/gtest.h>
#include "include/serial_communication.hpp"
#include "third_party/SerialLibrary/include/serial/serial.h"
#include <sys/time.h>

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

    vector<string> messages_to_send = {"f;-0.004883;0.090915;-0.309793;-1.000000;0.000000;0.000000;!", "a-a-a-a-a;!", "b-b-b-b-b;!", "c-c-c-c-c;!", "d-d-d-d-d;!", "e-e-e-e-e;!"};

    //vector<string> messages_to_send = {"a-a-a-a-a;!", "b-b-b-b-b;!", "c-c-c-c-c;!", "d-d-d-d-d;!", "e-e-e-e-e;!"};

};

TEST_F(SerialCommsTest, ConnectSerialSuccessfully){
    serialComm->connect_serial(0);
    sleep(1);
    serialComm->isSerialPortOpen();

    ASSERT_FALSE(serialComm->get_connecting());
}

TEST_F(SerialCommsTest, ReadandWriteMessageSuccessfully){
    serialComm->connect_serial(0);
    sleep(1);
    serialComm->isSerialPortOpen();
    
    for (size_t i = 0; i < messages_to_send.size(); i++){
        serialComm->publishToArduino(messages_to_send[i]);
    } 
    sleep(1);
    ASSERT_FALSE(serialComm->get_connecting());

}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}



