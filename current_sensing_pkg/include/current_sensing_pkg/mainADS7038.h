#ifndef MAINADS7038_H
#define MAINADS7038_H

class ADS7038{

    private:




public:


    int spi_fd_;
    const char* device_path_;
    uint8_t initSPI();
    uint8_t readRegister(uint8_t read_From);
    uint8_t writeRegister(uint8_t address, uint8_t data);
    uint8_t writeRegisterBits(uint8_t address, uint8_t mask);
    uint8_t clearBits(uint8_t address, uint8_t mask);
    uint8_t selCrystal(uint8_t mode);


    explicit ADS7038(const char* device_path = "/dev/spidev0.0");
    ~ADS7038();

    uint8_t init();
    uint8_t setChannelAnalogInput(uint8_t channelID);
    uint8_t reset();
    uint8_t calibrate();
    uint8_t setAppendID();
    uint8_t setAllChAnalog();
    uint8_t setStats();
    uint8_t startSequence();
    uint8_t stopSequence();
    void readStatus();
    uint8_t setChannelToSequence(uint8_t channels);
    uint8_t setOversampling(uint8_t mode);
    uint8_t setConvMode(uint8_t mode);
    uint8_t selSamplingSpeed(uint8_t mode);
    uint8_t setIndChannelCFG(uint8_t channelID, uint8_t mode);
    uint8_t setMulChannelCFG(uint8_t mode);
    float conversion(uint8_t LSB, uint8_t MSB);
    uint8_t setChIdManual(uint8_t channelID);
    float readRecent(uint8_t channelID);
    float readMax(uint8_t channelID);
    float readmin(uint8_t channelID);
    uint8_t setSeqModeManual();
    uint8_t setSeqModeAutoSequence();
    uint8_t setSeqModeOnTheFly();
    uint8_t setManual();
    uint8_t setAutoSeq();
    uint8_t setOnTheFly();
    uint8_t setAutonomous();
    uint8_t initModeAds7038(uint8_t mode);
    uint32_t readTest();
    


    



};
#endif