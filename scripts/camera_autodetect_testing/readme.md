# Camera System Documentation

## Dependencies 
### Linux (Jetson)
```bash
pip install pyudev
sudo apt install gstreamer1.0-tools
```

### Linux (Viewing)
```bash
sudo apt install gstreamer1.0-tools
```

---

## Running the Camera System

### Automatic Startup
The system runs automatically on startup.

### Manual Execution

#### Jetson Orin Nano
```bash
cd gpiotest
python3 mann-autostartcams.py
```

#### Jetson NX
```bash
cd camera_testing
python3 rtsp.py
```

---

## Stopping the System

### Hard Kill
```bash
ps -aux | grep gpiotest
kill -INT <pid>
```

---

## Viewing Camera Feeds

### RTSP Stream (Current)
```bash
gst-launch-1.0 rtspsrc location=rtsp://<IP>:8554/<CamName> latency=0 \
! rtph265depay ! h265parse ! autovideosink
```

**Example:**
```bash
gst-launch-1.0 rtspsrc location=rtsp://<IP>:8554/ArmCam latency=0 \
! rtph265depay ! h265parse ! autovideosink
```

### ROS (Currently Unused)
```bash
ros2 run rqt_image_view rqt_image_view
```
### Dashboard
>  **Work in progress**

---

## Notes
- Replace `<IP>` with your device's IP address
- Replace `<CamName>` with your camera's name
- Replace `<pid>` with the actual process ID from the `ps` command