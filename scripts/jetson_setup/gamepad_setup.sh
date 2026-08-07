#!/usr/bin/env bash

# Sets up support for a gamepad (e.g. Logitech F710) usage on the Jetson

set -e

sudo apt-get update && sudo apt-get install dkms
sudo git clone https://github.com/paroj/xpad.git /usr/src/xpad-0.4
sudo dkms install -m xpad -v 0.4
