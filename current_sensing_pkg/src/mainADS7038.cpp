#include <linux/spi/spidev.h>
#include <stdio.h>
#include <stdlib.h>
extern "C"{
    #include "/home/roverpc/Documents/current_sensing_pkg/include/current_sensing_pkg/ads7038.h"
}
#include <unistd.h>
#include <stdint.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <iostream>
#include "/home/roverpc/Documents/current_sensing_pkg/include/current_sensing_pkg/mainADS7038.h"
#include <cstring>




/*
* For reference, the ads can go up to 1000 kilo samples per seconds, so the tcycle is 1000 ns
* The aquisistion time is about 300 nS and the convertion time is 600 nS. close enough to 1000 ns with imprecisions and and other times (tquiet and others)
* so it takes about 1 ms to get data from one input, a break of 200 ns of cs high must be done between com requests
*/

// Value of the analog scale voltage.
#define AVDD 3

// global variables: change here the polarity of the signal, signal speed and signal frame
int mode = SPI_MODE_0;
/*
*SPI_MODE_0 --->   Cpol=0 (clock idle low) cpha=0 (rising edge)
*SPI_MODE_1 --->   Cpol=0 (clock idle low) cpha=1 (falling edge)
*SPI_MODE_2 --->   Cpol=1 (clock idle high) cpha=0 (rising edge)
*SPI_MODE_3 --->   Cpol=1 (clock idle high) cpha=1 (falling edge)
*/
int bits_per_word=8;//number of bits per words (self-explanatory) set to be the size of the ads's registers and 

int speed = 100000; //25 kHz

bool oversampling=false;
#define MANUAL_MODE  0
#define AUTO_SEQUENCE 1
#define ON_THE_FLY 2
#define AUTONOMOUS 3


ADS7038::ADS7038(const char* device_path)
: spi_fd_(-1), device_path_(device_path)
{}

ADS7038::~ADS7038(){
    if(spi_fd_>=0){
        close(spi_fd_);
    }
}

uint8_t ADS7038::init(){
    spi_fd_ =open("/dev/spidev1.0", O_RDWR);

    if(spi_fd_<0){//sends a error message to the terminal if it failed
        std::cerr <<"Failed to open the SPI communication on /dev/spidev0.0, use: ls /dev/spidev* to find all channels and make sure SPI is enabled on the jetson"<<std::endl;
        return 0;
    }
    
    return initSPI();
    
}

//using RDWR set for both read and write, I use it seperatly for error detection but could also do both at the same time


uint8_t ADS7038::initSPI(){

    //polarity
    if(ioctl(spi_fd_, SPI_IOC_RD_MODE, &mode)<0){//sets the signal format for reading
        std::cerr << "Error: failed to set the mode on READ"<<std::endl;
        close(spi_fd_);//closes the com if failed. just to be safe 
        return 0;
    }
    if(ioctl(spi_fd_, SPI_IOC_WR_MODE, &mode)<0){//sets the signal format for writing
        std::cerr << "Error: failed to set the mode on WRITE"<<std::endl;
        close(spi_fd_);//closes the com if failed. just to be safe 
        return 0;
    }
    int msb=0;
//msb message
    if(ioctl(spi_fd_, SPI_IOC_RD_LSB_FIRST, &msb)<0){//sets the signal format for reading
        std::cerr << "Error: failed to set the mode on READ"<<std::endl;
        close(spi_fd_);//closes the com if failed. just to be safe 
        return 0;
    }
    if(ioctl(spi_fd_, SPI_IOC_WR_LSB_FIRST, &msb)<0){//sets the signal format for writing
        std::cerr << "Error: failed to set the mode on WRITE"<<std::endl;
        close(spi_fd_);//closes the com if failed. just to be safe 
        return 0;
    }

    //bits per word
    if(ioctl(spi_fd_, SPI_IOC_WR_BITS_PER_WORD, &bits_per_word)){ //sets the the format the what is considered a word and how to package signal to send
        std::cerr << "Error: failed to set the bits per word on WRITE"<<std::endl;
        close(spi_fd_);//closes the com if failed. just to be safe 
        return 0;
    }
    if(ioctl(spi_fd_, SPI_IOC_RD_BITS_PER_WORD, &bits_per_word)){ //sets the the format the what is considered a word and how to package signal when reading
        std::cerr << "Error: failed to set the bits per word on READ"<<std::endl;
        close(spi_fd_);//closes the com if failed. just to be safe 
        return 0;
    }
    //speed
    if(ioctl(spi_fd_, SPI_IOC_WR_MAX_SPEED_HZ, &speed)){ //sets the the format the what is considered a word and how to package signal when reading
        std::cerr << "Error: failed to set the max speed on WRITE"<<std::endl;
        close(spi_fd_);//closes the com if failed. just to be safe 
        return 0;
    }
    if(ioctl(spi_fd_, SPI_IOC_RD_MAX_SPEED_HZ, &speed)){ //sets the the format the what is considered a word and how to package signal when reading
        std::cerr << "Error: failed to set the speed on READ" <<std::endl;
        close(spi_fd_);//closes the com if failed. just to be safe 
        return 0;
    }
    return 0;
}

uint8_t ADS7038::readRegister(uint8_t read_From){
    int attempts=0; // In case of errors
    int maxAttempts=3; //number of re-attempts for a total of 4 attempts
    int status;

    if(read_From >MAX_REGISTER_ADDRESS){
        return 0;
    };// aborts the program if the given register to read from does not exist
    /*
    * To read, the structure goes like this:
    * opcode to read ---> where to read --> dummy code (we need to send 24 bits, the ads structure is like that because of the write)
    * then on another structure, we get a new cycle (toggle cs) to get the content of the thing we went to read
    */


    uint8_t dataTx1[3],dataTx2[3]={0};// a forth element would be for crc, that we do not use here
    uint8_t dataRx1[3],dataRx2[3]={0};
    uint8_t numberOfBytes = 3;// as we said, crc is no on, so 3 not 4
    //bool crcError=false;//added it just because the exemple did, easy later on to modify.

    //go read section 7.3.12.2.2 for more info on the structure for sending data on the ads7038's datasheet
    dataTx1[0]=0b00010000;
    dataTx1[1]=read_From;
    dataTx1[2]=OPCODE_NULL;

    dataTx2[0]=0b00010000;
    dataTx2[1]=read_From;
    dataTx2[2]=OPCODE_NULL;


    struct spi_ioc_transfer transfer;
    memset(&transfer,0,sizeof(transfer));
    transfer.tx_buf=(unsigned long)dataTx1;
    transfer.rx_buf=(unsigned long)dataRx1;
    transfer.len=sizeof(dataTx1);
    transfer.speed_hz=400000;
    transfer.delay_usecs=0; //this is the bare minimum, technicaly we need 200 ns, usec does not do that we. could separate the structure but meh, same results
    transfer.bits_per_word=8;
    transfer.cs_change=0;
    
    status=ioctl(spi_fd_,SPI_IOC_MESSAGE(1),&transfer);

    

    struct spi_ioc_transfer transfer2;
    memset(&transfer2,0,sizeof(transfer2));

    transfer2.tx_buf=(unsigned long)dataTx2;
    transfer2.rx_buf=(unsigned long)dataRx2;
    transfer2.len=sizeof(dataTx2);
    transfer2.speed_hz=400000;
    transfer2.delay_usecs=0; //this is the bare minimum, technicaly we need 200 ns, usec does not do that we. could separate the structure but meh, same results
    transfer2.bits_per_word=8;
    transfer2.cs_change=0;

    status=ioctl(spi_fd_,SPI_IOC_MESSAGE(1),&transfer2);

     do {
        
         if(status<0){
             std::cerr<< "Error: failed to send data to the device. Trying again, "
             << attempts<< " re-attempts so far."<< std::endl;
             attempts++;
             usleep(1000);// delay of 1ms, kinda overkill, but meh
         }
         else{break;}
     }while(attempts<maxAttempts);

     if(status<0){
         std::cerr<< "Error: failed to send data to the device multiple time, check the wires."<< std::endl;
         return 0;
     }
    
    return dataRx1[0]+dataRx1[1]+dataRx1[2]+dataRx2[0]+dataRx2[1]+dataRx2[2];
}

uint8_t ADS7038::writeRegister(uint8_t address, uint8_t data){
    int attempts=0; // In case of errors
    int maxAttempts=3; //number of re-attempts for a total of 4 attempts
    int status;

    if(address > MAX_REGISTER_ADDRESS){
        return 0;
    };// aborts the program if the given register to read from does not exist

     /*
     * The write structure goes like that:
     * opcode to write ---> Where to write ---> what to write
     * for more info on the structure, go read section 7.3.12.2.1 of the datasheet of the ads7038 
     */

    uint8_t dataTx[3],dataRx[3]={0};//since the crc is not used, no fourth location
    uint8_t numberOfBytes = 3; //number of byte to send

    dataTx[0]=0b00001000;
    dataTx[1]=address;
    dataTx[2]=data;
    

    struct spi_ioc_transfer transfer;
    memset(&transfer,0,sizeof(transfer));
    transfer.tx_buf=(unsigned long)dataTx;
    transfer.rx_buf=(unsigned long)dataRx;
    transfer.len=sizeof(dataTx);
    transfer.speed_hz=400000;
    transfer.delay_usecs=0; //this is the bare minimum, technicaly we need 200 ns, usec does not do that we. could separate the structure but meh, same results
    transfer.bits_per_word=8;
    transfer.cs_change=0;
    

    /*do {
        status=ioctl(spi_fd_,SPI_IOC_MESSAGE(1),&transfer);
        if(status<0){
            std::cerr<< "Error: failed to send data to the device. Trying again, "
            << attempts<< " re-attempts so far."<< std::endl;
            attempts++;
            usleep(1000);// delay of 1ms, kinda overkill, but meh
        }
        else{break;}
    }while(attempts<maxAttempts);*/

    /*if(status<0){
        std::cerr<< "Error: failed to send data to the device multiple time, check the wires."<< std::endl;
        return 0;
    }*/
    ioctl(spi_fd_,SPI_IOC_MESSAGE(1),&transfer);
    return 1;

}

uint32_t ADS7038::readTest(){
    int attempts=0; // In case of errors
    int maxAttempts=3; //number of re-attempts for a total of 4 attempts
    int status;

    /*
    * To read, the structure goes like this:
    * opcode to read ---> where to read --> dummy code (we need to send 24 bits, the ads structure is like that because of the write)
    * then on another structure, we get a new cycle (toggle cs) to get the content of the thing we went to read
    */


    uint8_t dataTx[3]={0};// a forth element would be for crc, that we do not use here
    uint8_t dataRx[3]={0};
    uint8_t numberOfBytes = 3;// as we said, crc is no on, so 3 not 4
    //bool crcError=false;//added it just because the exemple did, easy later on to modify.
    dataTx[0]=OPCODE_NULL;
    dataTx[1]=OPCODE_NULL;
    dataTx[2]=OPCODE_NULL;

    struct spi_ioc_transfer transfer ={
        .tx_buf=(unsigned long) dataTx,
        .rx_buf=(unsigned long) dataRx,
        .len= sizeof(dataTx),
    };

    do {
        status=ioctl(spi_fd_,SPI_IOC_MESSAGE(1),&transfer);
        if(status<0){
            std::cerr<< "Error: failed to send data to the device. Trying again, "
            << attempts<< " re-attempts so far."<< std::endl;
            attempts++;
            usleep(1000);// delay of 1ms, kinda overkill, but meh
        }
        else{break;}
    }while(attempts<maxAttempts);

    if(status<0){
        std::cerr<< "Error: failed to send data to the device multiple time, check the wires."<< std::endl;
        return 0;
    }

    if(dataRx==nullptr){
       return 0;
    };//paranoiac
    
    uint32_t ans  =  ((uint32_t)dataRx[0] << 16) | ((uint32_t) dataRx[1] << 8) | ((uint32_t) dataRx[2] );
    return ans;
}

uint8_t ADS7038::writeRegisterBits(uint8_t address, uint8_t mask){

    int attempts=0; // In case of errors
    int maxAttempts=3; //number of re-attempts for a total of 4 attempts
    int status;

    if(address>MAX_REGISTER_ADDRESS){
        return 0;
    }; // aborts the program if the given register to read from does not exist

    /*
    * The format is like the one for writing but with a bit masking opcode.
    */

    uint8_t dataTx[3],dataRx[3]={0}; //only 3 because we dont use crc here, the fourth one would be for the crc byte
    uint8_t numberOfBytes =3; //we send 3 bytes because we dont have crc
    //for more detail on the format, go read the datasheet of the ads7038 section 7.3.12.2

    dataTx[0]=OPCODE_SETBIT;
    dataTx[1]=address;
    dataTx[2]=mask;

    struct spi_ioc_transfer transfer ={
        .tx_buf=(unsigned long) dataTx,
        .rx_buf=(unsigned long) dataRx,
        .len= sizeof(dataTx),
    };

    do {
        status=ioctl(spi_fd_,SPI_IOC_MESSAGE(1),&transfer);
        if(status<0){
            std::cerr<< "Error: failed to send data to the device. Trying again, "
            << attempts<< " re-attempts so far."<< std::endl;
            attempts++;
            usleep(1000);// delay of 1ms, kinda overkill, but meh
        }
        else{break;}
    }while(attempts<maxAttempts);

    if(status<0){
        std::cerr<< "Error: failed to send data to the device multiple time, check the wires."<< std::endl;
        return 0;
    }

    return 1;

}

uint8_t ADS7038::clearBits(uint8_t address, uint8_t mask){

    int attempts=0; // In case of errors
    int maxAttempts=3; //number of re-attempts for a total of 4 attempts
    int status;

    if(address>MAX_REGISTER_ADDRESS){
        return 0;
    }; // aborts the program if the given register to read from does not exist

    /*
    * The format is like the one for writing but with a bit masking opcode.
    */

    uint8_t dataTx[3],dataRx[3]={0}; //only 3 because we dont use crc here, the fourth one would be for the crc byte
    uint8_t numberOfBytes =3; //we send 3 bytes because we dont have crc
    //for more detail on the format, go read the datasheet of the ads7038 section 7.3.12.2

    dataTx[0]=OPCODE_CLRBIT;
    dataTx[1]=address;
    dataTx[2]=mask;

    struct spi_ioc_transfer transfer ={
        .tx_buf=(unsigned long) dataTx,
        .rx_buf=(unsigned long) dataRx,
        .len= sizeof(dataTx),
    };

    do {
        status=ioctl(spi_fd_,SPI_IOC_MESSAGE(1),&transfer);
        if(status<0){
            std::cerr<< "Error: failed to send data to the device. Trying again, "
            << attempts<< " re-attempts so far."<< std::endl;
            attempts++;
            usleep(1000);// delay of 1ms, kinda overkill, but meh
        }
        else{break;}
    }while(attempts<maxAttempts);

    if(status<0){
        std::cerr<< "Error: failed to send data to the device multiple time, check the wires."<< std::endl;
        return 0;
    }

    return 1;
}

uint8_t ADS7038::setChannelAnalogInput(uint8_t channelID){
    if(channelID <8){
        return 0;
    };//we have 7, channels 0-7

    return clearBits(PIN_CFG_ADDRESS,(1<<channelID));
}

uint8_t ADS7038::reset(){
       if(writeRegisterBits(GENERAL_CFG_ADDRESS,GENERAL_CFG_CH_RST_MASK)<=0){

        return 0;
   }

    usleep(50000); //wait for the ads to stabilize, data sheet says minimum 5 ms, I give 50 ms, change my mind.

    if(writeRegisterBits(SYSTEM_STATUS_ADDRESS, SYSTEM_STATUS_BOR_MASK)<=0){ //clears the bor bit, yes you write 1 to clear, it is not a mistake, thats how you reset it.
        return 0;
    }

    return 1;
}

uint8_t ADS7038::calibrate(){
       if(writeRegisterBits(GENERAL_CFG_ADDRESS,GENERAL_CFG_CH_RST_MASK)<=0){
        return 0;
   }

    usleep(5000); //I assume calibrating takes the same amount of time as power up, it does not, but i dont know for sure. Datasheet does not say.
    
    return 1;
}

uint8_t ADS7038::setAppendID(){
    return writeRegisterBits(DATA_CFG_ADDRESS,DATA_CFG_APPEND_STATUS_FOUR_BIT_CHID);// The output data comes out with 4 bits with the channel ID. 

}

uint8_t ADS7038::setAllChAnalog(){
    return writeRegisterBits(GENERAL_CFG_ADDRESS, GENERAL_CFG_CH_RST_SET_ALL_CH_AS_ANALOG_INPUTS);
}

uint8_t ADS7038::setStats(){
    return writeRegisterBits(GENERAL_CFG_ADDRESS, GENERAL_CFG_STATS_EN_STATS_ENABLED);
}

uint8_t ADS7038::startSequence(){
    return writeRegisterBits(SEQUENCE_CFG_ADDRESS, SEQUENCE_CFG_SEQ_START_ENABLED);
}

uint8_t ADS7038::stopSequence(){
    return writeRegisterBits(SEQUENCE_CFG_ADDRESS, SEQUENCE_CFG_SEQ_START_DISABLED);
}

/*
* Init is the location where the 4 modes will be selected
* Manual mode --->                implemented  ---> give param MANUAL
* Auto-sequence mode --->         implemented ----> give param AUTO_SEQUENCE
* on the fly mode --->            not implemented
* Autonomous mode --->            not implemneted
*/

void ADS7038::readStatus(){

    uint8_t registerStatus=readRegister(SYSTEM_STATUS_ADDRESS);// from there, we read the seq_status, the crc flags on power up, crc error status and the brown out status
    uint8_t generalRegister= readRegister(GENERAL_CFG_ADDRESS); // from there, we read crc status, stats recording status, digital window comparator, chanel rst, calibration status and rst status
    uint8_t dataRegister=readRegister(DATA_CFG_ADDRESS); // from there, we get the append status, fix pat status and spi polarity
    uint8_t osrRegister=readRegister(OSR_CFG_ADDRESS); // from there, we get the oversampling ratio
    uint8_t opmodeRegister=readRegister(OPMODE_CFG_ADDRESS); // from there, we get the behavior in auto mode when crc error detected, the conversion mode, the crystal selected the sampling speed in auto mode
    uint8_t pinConfiguration =readRegister(PIN_CFG_ADDRESS); // from there, we get the gpio/analogue status for each channels
    uint8_t sequenceRegister = readRegister(SEQUENCE_CFG_ADDRESS); // from there, we get the status mode of the auto sequence mode and we get the mode that the adc is operating in.
    uint8_t SelectChannelRegister=readRegister(CHANNEL_SEL_ADDRESS); // next channel to read in manual mode
    uint8_t autoSequChannelSelect =readRegister(AUTO_SEQ_CHSEL_ADDRESS); // from there, we get the channels that will be cycled in auto sequence mode

    //Analyse the status register
    std::cout<< "Reading the Status register:" <<std::endl;
    if(registerStatus<=0){
        std::cout<< "Could not read the Status register" <<std::endl;
    }else {
        uint8_t seq_status= ((registerStatus & SYSTEM_STATUS_SEQ_STATUS_MASK) >>6); //masks all the bits concerned and moves those in the front so that we can read them.
        uint8_t crcerr_fuse = ((registerStatus & SYSTEM_STATUS_CRCERR_FUSE_MASK)>>2);// the >>N says, move all the bits to the right by a factor of N and N is the location of the the element we are looking for.
        uint8_t crcerr_in = ((registerStatus & SYSTEM_STATUS_CRCERR_IN_MASK)>>1); 
        uint8_t bor = (registerStatus & SYSTEM_STATUS_BOR_MASK);

        std::cout<< "Status of the channel sequencer: ";//tells if the auto sequence mode is running or not
        switch(seq_status){
            case 0:
                std::cout<< "Sequence stoped." << std::endl;
                break;
            case 1:
                std::cout<< "Sequence is in progress."<<std::endl;
                break;
        }

        std::cout<< "Status of CRC configuration on power up: ";//tells if the crc was configured properly on power up
        switch(crcerr_fuse){
            case 0:
                std::cout<< "No problem detected in power up configuration." << std::endl;
                break;
            case 1:
                std::cout<< "Device configuration not loaded properly"<<std::endl;
                break;
        }

        std::cout<< "Status of the CRC on the incomming data: ";//tells if the a crc error was detected
        switch(crcerr_in){
            case 0:
                std::cout<< "No CRC error." << std::endl; 
                break;
            case 1:
                std::cout<< "CRC error detected. (writes disabled until cleared)"<<std::endl;//*CAUTION* ALL WRITES WILL BE LOCKED OF THIS BIT IS 1 EXCEPT FOR THE REGISTER 0X00 AND 0X01.
                break;
        }

        std::cout<< "Status of the Brown out rst indicator: ";// indicate if a brown out is detected.
        switch(bor){
            case 0:
                std::cout<< "No brown out detedted so far." << std::endl;
                break;
            case 1:
                std::cout<< "Brown out detected or device rst."<<std::endl;
                break;
        }
    }
    //Analyse the general register
    std::cout<< "Reading the General register:" <<std::endl;   
    if(generalRegister<=0){
        std::cout<< "Could not read the General register" <<std::endl;
    }else {
        uint8_t CRC_EN= ((generalRegister & GENERAL_CFG_CRC_EN_MASK) >>6); 
        uint8_t STATS_EN = ((generalRegister & GENERAL_CFG_STATS_EN_MASK)>>5);
        uint8_t DWC_EN = ((generalRegister & GENERAL_CFG_DWC_EN_MASK)>>4); 
        uint8_t CH_RST = ((generalRegister & GENERAL_CFG_CH_RST_MASK)>>2);
        uint8_t CAL = ((generalRegister & GENERAL_CFG_CAL_MASK)>>1); 
        uint8_t RST = (generalRegister & GENERAL_CFG_RST_MASK);

        std::cout<< "Status of the CRC: ";//tells if crc is running or not
        switch(CRC_EN){
            case 0:
                std::cout<< "CRC module disabled." << std::endl;
                break;
            case 1:
                std::cout<< "CRC module is enabled on incoming data, data is appended on output."<<std::endl;
                break;
        }

        std::cout<< "Status of the statistics collector: ";//tells if the max and mins are collected and recent
        switch(STATS_EN){
            case 0:
                std::cout<< "Statistics disabled." << std::endl;
                break;
            case 1:
                std::cout<< "Statistic is enabled."<<std::endl;//writing 1 to this bit, will wipe the current max/min/recent to reset
                break;
        }

        std::cout<< "Status of the digital window comparator: ";//self-explanatory
        switch(DWC_EN){
            case 0:
                std::cout<< "Desabled DWC." << std::endl;
                break;
            case 1:
                std::cout<< "DWC enabled."<<std::endl;
                break;
        }

        std::cout<< "Status of channel overwrite bit: ";// when set to one, all the inputs are force to be analog inputs no matter what the other registers are saying
        switch(CH_RST){
            case 0:
                std::cout<< "Normal operation." << std::endl;
                break;
            case 1:
                std::cout<< "All channels are analog inputs."<<std::endl;
                break;
        }


        std::cout<< "Status of the calibration bit: ";//self-explanatory
        switch(CAL){
            case 0:
                std::cout<< "The ADC is calibrated." << std::endl;
                break;
            case 1:
                std::cout<< "The ADC is calibrating."<<std::endl;
                break;
        }

        std::cout<< "Status of RST bit: ";//self-explanatory
        switch(RST){
            case 0:
                std::cout<< "Normal operation." << std::endl;
                break;
            case 1:
                std::cout<< "The device is reset."<<std::endl;
                break;
        }
    }
    //Analyse the Data register
    std::cout<< "Reading the Data register:" <<std::endl;   
    if(dataRegister<=0){
        std::cout<< "Could not read the data register" <<std::endl;
    }else {
        uint8_t FIX_PAT= ((dataRegister & DATA_CFG_FIX_PAT_MASK) >>7); 
        uint8_t APPEND_STATUS = ((dataRegister & DATA_CFG_APPEND_STATUS_MASK)>>4);
        uint8_t CPOL_CPHA = (dataRegister & DATA_CFG_CPOL_CPHA_MASK); 
        
        std::cout<< "Status of the fix pat for debugging: ";//only outputs the sequence 0xA5A
        switch(FIX_PAT){
            case 0:
                std::cout<< "Normal operation." << std::endl;
                break;
            case 1:
                std::cout<< "Device output fixed to 0xA5A."<<std::endl;//if it's fixed, how tf are u getting that
                break;
        }

        std::cout<< "Status of the append: ";//tells if if and what is appended to the end of the output data
        switch(APPEND_STATUS){
            case 0:
                std::cout<< "Nothing is appended." << std::endl;
                break;
            case 1:
                std::cout<< "4-bit channel ID is appended to the ADC data."<<std::endl;
                break;
            case 2:
                std::cout<< "4-bit status flag is appended." << std::endl;
                break;
            case 3:
                std::cout<< "reserved."<<std::endl; //??
                break;
        }

        std::cout<< "Status of the polarity: ";// tells you the polarity and aquisition of the signals used for spi
        switch(CPOL_CPHA){
            case 0:
                std::cout<< "CPOL=0, CPHA=0." << std::endl;
                break;
            case 1:
                std::cout<< "CPOL=0, CPHA=1."<<std::endl;
                break;
            case 2:
                std::cout<< "CPOL=1, CPHA=0." << std::endl;
                break;
            case 3:
                std::cout<< "CPOL=1, CPHA=1."<<std::endl; 
                break;
        }
    }

    //Analyse the oversampling register
    std::cout<< "Reading the Oversampling register:" <<std::endl;   
    if(osrRegister<=0){
        std::cout<< "Could not read the oversampling register" <<std::endl;
    }else {
        uint8_t OSR= (osrRegister & OSR_CFG_OSR_MASK); 

        std::cout<< "Status of the oversampling ratio: ";//tells if the auto sequence mode is running or not
        switch(OSR){
            case 0:
                std::cout<< "No averaging." << std::endl;
                break;
            case 1:
                std::cout<< "2 samples."<<std::endl;
                break;
            case 2:
                std::cout<< "4 samples." << std::endl;
                break;
            case 3:
                std::cout<< "8 samples."<<std::endl; 
                break;
            case 4:
                std::cout<< "16 samples." << std::endl;
                break;
            case 5:
                std::cout<< "32 samples."<<std::endl;
                break;
            case 6:
                std::cout<< "64 samples." << std::endl;
                break;
            case 7:
                std::cout<< "128 samples."<<std::endl; 
                break;
        }

    }

    //Analyse the opmode register
    std::cout<< "Reading the OPMODE register:" <<std::endl;   
    if(opmodeRegister<=0){
        std::cout<< "Could not read the opmode register" <<std::endl;
    }else {
        uint8_t conv_on_err= ((opmodeRegister & OPMODE_CFG_CONV_ON_ERR_MASK)>>7); 
        uint8_t conv_mode= ((opmodeRegister & OPMODE_CFG_CONV_MODE_MASK)>>5); 
        uint8_t osc_sel= ((opmodeRegister & OPMODE_CFG_OSC_SEL_MASK)>>4); 
        uint8_t clk_div= (opmodeRegister & OPMODE_CFG_CLK_DIV_MASK); 

        std::cout<< "Steps to take when CRC detected on autonomous mode: ";//tells what to do when you are in autonomous mode and there is a CRC error in the line
        switch(conv_on_err){
            case 0:
                std::cout<< "If CRC detected, continues and keeps it configuration." << std::endl;
                break;
            case 1:
                std::cout<< "Changes all channels to analog inputs and sequencing is paused."<<std::endl;//the configuration is restored after removing the crc_in flag
                break;
        }

        std::cout<< "Status of the mode of conversion: ";
        switch(conv_mode){
            case 0:
                std::cout<< "Manual mode." << std::endl;
                break;
            case 1:
                std::cout<< "Autonomous mode."<<std::endl;
                break;
        }

        std::cout<< "Status of the internal oscillator: ";
        switch(osc_sel){
            case 0:
                std::cout<< "High-speed." << std::endl;
                break;
            case 1:
                std::cout<< "Low-power."<<std::endl;
                break;
        }

        std::cout<< "Status of the option level of the sampling speed: ";
        std::cout<< "Option " << clk_div << "."<< std::endl;
        
    }

    //Analyse the PIN configuration register
    std::cout<< "Reading the Pin configuration register:" <<std::endl;  //tells you the configuration of each channels 
    if(pinConfiguration<=0){
        std::cout<< "Could not read the pin configuration register" <<std::endl;
    }else {
        uint8_t pinCFG[8]={0};
        pinCFG[7]= ((pinConfiguration >>7) & 0x01); //custom mask to get only the bit we need to know if the channel is analog or gpio
        pinCFG[6]= ((pinConfiguration >>6) & 0x01); 
        pinCFG[5]= ((pinConfiguration >>5) & 0x01); 
        pinCFG[4]= ((pinConfiguration >>4) & 0x01); 
        pinCFG[3]= ((pinConfiguration >>3) & 0x01); 
        pinCFG[2]= ((pinConfiguration >>2) & 0x01); 
        pinCFG[1]= ((pinConfiguration >>1) & 0x01); 
        pinCFG[0]= (pinConfiguration & 0x01); 

        for(int i=0;i<8; i++){
            std::cout<< "Channel ID "<<i<<" is ";
            switch(pinCFG[i]){
                case 0:
                    std::cout<< "an analog input." << std::endl;
                    break;
                case 1:
                    std::cout<< "a GPIO." << std::endl;
                    break;
            }   
        }
    }

    //Analyse the sequence configuration register
    std::cout<< "Reading the squence configuration register:" <<std::endl;  //tells you sequence settings
    if(sequenceRegister<=0){
        std::cout<< "Could not read the sequence configuration register" <<std::endl;
    }else {
        uint8_t SEQ_START= ((opmodeRegister & SEQUENCE_CFG_SEQ_START_MASK)>>4); 
        uint8_t SEQ_MODE= (opmodeRegister & SEQUENCE_CFG_SEQ_MODE_MASK); 

        std::cout<< "Status of the sequencing: ";//channel sequence when in auto sequence mode
        switch(SEQ_START){
            case 0:
                std::cout<< "Sequencing stopped." << std::endl;
                break;
            case 1:
                std::cout<< "Sequencing enabled in ascending order."<<std::endl;
                break;
        }

        std::cout<< "Status of the sequence mode: ";//tells you how the sequence is selected
        switch(SEQ_MODE){
            case 0:
                std::cout<< "Manual mode sequence, channel is selected via MANUAL_CHID." << std::endl;
                break;
            case 1:
                std::cout<< "Auto sequence mode, channel is selected in AUTO_SEQ_CHSEL."<<std::endl;
                break;
            case 2:
                std::cout<< "On the fly sequence mode." << std::endl;
                break;
            case 3:
                std::cout<< "reserved."<<std::endl; //??
                break;
        }
    }

    //Analyse the Channel select configuration register
    std::cout<< "Reading the channel select in manual mode configuration register:" <<std::endl;  //tells you the next channel to be probed in manual mode
    if(SelectChannelRegister<=0){
        std::cout<< "Could not read the channel select in manual mode configuration register" <<std::endl;
    }else {
        uint8_t MANUAL_CHID=(SelectChannelRegister & CHANNEL_SEL_MANUAL_CHID_MASK);//lsb 4 should be 0

        std::cout<< "Channel selected: ";//tells you the selected channel for the next manual operation
        std::cout <<"Channel "<<MANUAL_CHID<<std::endl;
    }

    //Analyse the selected channels for sequencing configuration register
    std::cout<< "Reading the slected channels for sequencing configuration register:" <<std::endl;  //tells you the configuration of each channels 
    if(autoSequChannelSelect<=0){
        std::cout<< "Could not read the selected channels for sequencing configuration register" <<std::endl;
    }else {
        uint8_t SEQSEL[8]={0};
        SEQSEL[7]= ((autoSequChannelSelect >>7) & 0x01); //custom mask to get only the bit we need to know which channel is sequenced
        SEQSEL[6]= ((autoSequChannelSelect >>6) & 0x01); 
        SEQSEL[5]= ((autoSequChannelSelect >>5) & 0x01); 
        SEQSEL[4]= ((autoSequChannelSelect >>4) & 0x01); 
        SEQSEL[3]= ((autoSequChannelSelect >>3) & 0x01); 
        SEQSEL[2]= ((autoSequChannelSelect >>2) & 0x01); 
        SEQSEL[1]= ((autoSequChannelSelect >>1) & 0x01); 
        SEQSEL[0]= (autoSequChannelSelect & 0x01); 

        if(autoSequChannelSelect==0){
            std::cout<<"No channels selected for sequencing"<<std::endl;
        }else{
            for(int i=0;i<8; i++){
                if(SEQSEL[i]!=0){
                    std::cout<<"Channel "<<i<<" selected."<<std::endl;
                } 
            }
        }
    }

    
}

uint8_t ADS7038::setChannelToSequence(uint8_t channels){ //this function takes an eight bits value ex.: 0b00110000 where the 1 are the channels enaabled for sequencing
    return writeRegister(AUTO_SEQ_CHSEL_ADDRESS,channels);
}


//go see section 8.1.4 to see what mode does what
uint8_t ADS7038::setOversampling(uint8_t mode){ //takes a number between 0 and 7
    if(mode<0||mode>7){
        std::cerr<<"Invalid parameter given for oversampling"<<std::endl;
    }
    if(mode>0){
        oversampling=true;
    }

    return writeRegisterBits(OSR_CFG_ADDRESS,mode);
}
//changes the mode of conversion
//could also have done it by saying that we write the mode and we just look if mode is in bound, but i dont care enough
uint8_t ADS7038::setConvMode(uint8_t mode){ //take the number 0 and 3--> go see the define at the beggining for the reason

    switch(mode){
        case 0:
            return writeRegisterBits(OPMODE_CFG_ADDRESS,OPMODE_CFG_CONV_MODE_MANUAL_MODE);
        case 3:
            return writeRegisterBits(OPMODE_CFG_ADDRESS,OPMODE_CFG_CONV_MODE_AUTONOMOUS_MODE);
        default:
            std::cerr<<"Invalid parameter for the conversion mode selector"<<std::endl;
            return 0;
    }

}
//the mode is the bit to write to the register
uint8_t ADS7038::selCrystal(uint8_t mode){//more of an internal function, not really for user, but meh.
    if(mode<0||mode>1){
        std::cerr<<"Invalid parameter for the selction of the crystal"<<std::endl;
        return 0;
    }
    return writeRegisterBits(OPMODE_CFG_ADDRESS, mode);
}

uint8_t ADS7038::selSamplingSpeed(uint8_t mode){
    if(mode<0||mode>15){
        std::cerr<<"Invalid parameter for the sampling speed"<<std::endl;
        return 0;
    }
    return writeRegisterBits(OPMODE_CFG_ADDRESS,mode);
}
//sets the role to an idividual channel
uint8_t ADS7038::setIndChannelCFG(uint8_t channelID, uint8_t mode){//mode is 0 to set analog and 1 is GPIO
    if(channelID<0||channelID>7||mode<0||mode>1){
        std::cerr<<"Invalid parameter for the channel setting"<<std::endl;
        return 0;
    }

    return writeRegisterBits(PIN_CFG_ADDRESS,(mode<<channelID));
}

//sets multiple channels at the same time
uint8_t ADS7038::setMulChannelCFG(uint8_t mode){//takes a byte with the allready set desired configuration
    return writeRegister(PIN_CFG_ADDRESS,mode);
}

//takes the output data of the adc and converts it into a value we can understand
float ADS7038::conversion(uint8_t LSB, uint8_t MSB){//this function assumes the data is formated to contain only the results, no flag or id
    float numBits=65536;//   assumes oversampling is true
    uint16_t num=((uint16_t)MSB<<8)|LSB;// does ex.: msb: 0x85--> 0x8500 and then lsb: 0x12 ---> 0x8512
    if(!oversampling){
        num=num>>4;
        numBits=4096;

    }
    float current=(float)(num*(AVDD/numBits));
    current=current-(3.3*0.1);//3.3*0.1 is the supply voltage of the current sensor *0.1 which is the level where the current is 0 A (offset) and the output of the current sensor is 3.3*0.1
    current=(current/(0.08));//sensibility of the current sensor in mV we need V
    return current;
}

uint8_t ADS7038::setChIdManual(uint8_t channelID){
    if(channelID<0||channelID>7){
        std::cerr<<"Invalid channel ID"<<std::endl;
        return 0;
    }
    return writeRegister(CHANNEL_SEL_ADDRESS,channelID);
}



float ADS7038::readRecent(uint8_t channelID){
    if(channelID<0||channelID>7){
        std::cerr<<"Invalid channel ID"<<std::endl;
        return 0;
    }
    uint8_t LSB=readRegister(RECENT_CH0_LSB_ADDRESS+(2*channelID));
    uint8_t MSB=readRegister(RECENT_CH0_LSB_ADDRESS+(2*channelID)+1);

    return conversion(LSB,MSB);

}

float ADS7038::readMax(uint8_t channelID){
    if(channelID<0||channelID>7){
        std::cerr<<"Invalid channel ID"<<std::endl;
        return 0;
    }
    uint8_t LSB=readRegister(MAX_CH0_LSB_ADDRESS+(2*channelID));
    uint8_t MSB=readRegister(MAX_CH0_MSB_ADDRESS+(2*channelID)+1);

    return conversion(LSB,MSB);

}

float ADS7038::readmin(uint8_t channelID){
    if(channelID<0||channelID>7){
        std::cerr<<"Invalid channel ID"<<std::endl;
        return 0;
    }
    uint8_t LSB=readRegister(MIN_CH0_LSB_ADDRESS+(2*channelID));
    uint8_t MSB=readRegister(MIN_CH0_MSB_ADDRESS+(2*channelID)+1);

    return conversion(LSB,MSB);
}

uint8_t ADS7038::setSeqModeManual(){
    return writeRegisterBits(SEQUENCE_CFG_ADDRESS,SEQUENCE_CFG_SEQ_MODE_MANUAL);
}

uint8_t ADS7038::setSeqModeAutoSequence(){
    return writeRegisterBits(SEQUENCE_CFG_ADDRESS,SEQUENCE_CFG_SEQ_MODE_AUTO_SEQ);
}

uint8_t ADS7038::setSeqModeOnTheFly(){
    return writeRegisterBits(SEQUENCE_CFG_ADDRESS,SEQUENCE_CFG_SEQ_MODE_ON_THE_FLY);
}

uint8_t ADS7038::setManual(){
    
    reset();

    if(setAllChAnalog()<=0){
        return 0;
    }
    if(setConvMode(MANUAL_MODE)<=0){
        return 0;
    }
    if(setSeqModeManual()<=0){
        return 0;
    }
   

    return 1;
}

uint8_t ADS7038::setAutoSeq(){

    reset();

    if(setAllChAnalog()<=0){
        return 0;
    }
    
    if(setChannelToSequence(0xFF)<=0){
        return 0;
    }

    if(setSeqModeAutoSequence()<=0){
        return 0;
    }
    
    if(setConvMode(MANUAL_MODE)<=0){
        return 0;
    }

    if(setAppendID()<=0){
        return 0;
    }

    return 1;
}
uint8_t ADS7038::setOnTheFly(){//not implemented
    return 1;
}
uint8_t ADS7038::setAutonomous(){//not implemented
    return 1;
}

uint8_t ADS7038::initModeAds7038(uint8_t mode){

    if(mode<0||mode>3){
        std::cerr<<"Invalid mode parameter"<<std::endl;
        return 0;
    }

    usleep(50000);//delay time for power supply setting

    if(reset()<=0){
        return 0;
    }
    if(calibrate()<=0){
        return 0;
    }

    

    switch (mode)
    {
    case 0:
         setManual();
         break;
    case 1:
        setAutoSeq();
        break;
    case 2:
        setOnTheFly();
        break;
    default:
        setAutonomous();
        break;
    }
    
    readStatus();//big function that scan the status of the ads7038

}




