# Config Files

## Symlink `.rules` file

The `99-usb-serial.rules` file contains the rules that allow Arduinos that are plugged into the rover computer via USB to be identified with symlinks.

To use it, open the existing rules file on the Ubuntu computer using `sudo nano /etc/udev/rules.d/99-usb-serial.rules`. Then copy and paste the contents of `99-usb-serial.rules` into the opened `.rules` file and save it. Reload the udev rules by running `udevadm control --reload-rules`. The Arduinos should now be identified via symlinks when plugged in.

Also reference the existing wiki page explaining symlinks:

https://gitlab.com/uorover/rover_workspace/-/wikis/How-To/Rover-Computer-Setup#symbolic-links

More info. on creating symlinks [here](https://msadowski.github.io/linux-static-port/)

### Nano Symlinks

The symlink used to identify the drive Arduino Nano (named `drive_nano`) doesn't identify the Nano via the serial number. It uses `ATTRS{idProduct}`. The Arduino Nano that we have doesn't seem to have a serial number to be used for identification in the symlink. This _could_ be because it's not a genuine Arduino Nano and uses the CH340 chip, according to [this](https://arduino.stackexchange.com/questions/6617/setting-serial-number-on-ch340-usb-serial-device) stackexchange post.

If more Arduino Nanos were to be used that don't have serial numbers to be identified by, this could become a problem. The current symlink for the Nano could mistakenly identify another Arduino Nano as the `drive_nano`. The following links could be helpful to find workarounds:

https://arduino.stackexchange.com/a/31958

https://arduino.stackexchange.com/a/14668

https://docs.arduino.cc/learn/programming/eeprom-guide

https://playground.arduino.cc/Linux/Udev/
