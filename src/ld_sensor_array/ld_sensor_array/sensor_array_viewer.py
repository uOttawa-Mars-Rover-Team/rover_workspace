import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import NavSatFix  # Import for GPS data
import matplotlib.pyplot as plt
from collections import deque
import time
import math
import os
import csv
from datetime import datetime

# Define the path for saving data, expanding the user's home directory
dataPath = os.path.expanduser("~/rover_workspace/src/ld_sensor_array/data/")

class SensorArrayViewer(Node):
    def __init__(self):
        super().__init__("sensor_array_viewer")

        # --- Subscriptions ---
        # Subscription for Hydrogen and Ozone data
        self.subscription = self.create_subscription(
            String, "sensorData", self.plot_sensor_data, 10
        )
        # Subscription for GPS data
        self.gps_subscription = self.create_subscription(
            NavSatFix, "rover/fix", self.gps_callback, 10
        )
        # Subscription for Geiger counter data
        self.geiger_subscription = self.create_subscription(
            String, "/geiger/data", self.geiger_callback, 10
        )

        # --- Data Buffers for Plotting ---
        self.buffer_size = 50
        self.hydrogen_data = deque(maxlen=self.buffer_size)
        self.ozone_data = deque(maxlen=self.buffer_size)
        self.time_data = deque(maxlen=self.buffer_size)
        self.start_time = None

        # --- Storage for Latest Data for CSV Logging ---
        self.current_latitude = None
        self.current_longitude = None
        self.current_geiger_data = None

        # --- Live Plot Setup ---
        plt.ion()
        self.fig, self.ax1 = plt.subplots()
        self.ax2 = self.ax1.twinx()
        self.h_line, = self.ax1.plot([], [], 'b-', label='Hydrogen (ppm)')
        self.o_line, = self.ax2.plot([], [], 'r-', label='Ozone (ppb)')
        self.ax1.set_ylim(0, 500)
        self.ax2.set_ylim(0, 500)
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Hydrogen (ppm)", color='blue')
        self.ax2.set_ylabel("Ozone (ppb)", color='red')
        self.ax1.set_title("Live Sensor Readings")
        self.ax1.set_xticks([])
        self.ax1.legend(loc='upper left')
        self.ax2.legend(loc='upper right')

        # --- CSV File Setup ---
        self.csv_file = None
        self.csv_writer = None
        self.setup_csv_logging()

        # --- Timers ---
        # Timer for updating the plot
        self.plot_timer = self.create_timer(0.1, self.update_plot)
        # Timer for writing to CSV every 0.5 seconds
        self.logging_timer = self.create_timer(0.5, self.log_data_to_csv)

    def setup_csv_logging(self):
        """Prepares the CSV file for logging."""
        try:
            # Create the directory if it doesn't exist
            os.makedirs(dataPath, exist_ok=True)
            
            # Generate a unique filename with a timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filepath = os.path.join(dataPath, f"sensor_log_{timestamp}.csv")
            
            # Open the file and create a CSV writer
            # Using newline='' is important to prevent extra blank rows
            self.csv_file = open(filepath, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Write the header row
            header = ['timestamp', 'geiger_cps', 'ozone_ppb', 'hydrogen_ppm', 'latitude', 'longitude']
            self.csv_writer.writerow(header)
            self.get_logger().info(f"Logging data to {filepath}")

        except Exception as e:
            self.get_logger().error(f"Failed to set up CSV logging: {e}")

    # --- Sensor Data Callbacks ---

    def gps_callback(self, msg):
        """Callback for GPS data from 'rover/fix'."""
        self.current_latitude = msg.latitude
        self.current_longitude = msg.longitude
    
    def geiger_callback(self, msg):
        """Callback for Geiger data from '/geiger/data'."""
        self.current_geiger_data = msg.data.strip()

    def plot_sensor_data(self, msg):
        """Callback for Hydrogen/Ozone data from 'sensorData'."""
        try:
            data = msg.data.strip()
            hydrogen_str, ozone_str = data.split(";")
            hydrogen = float(hydrogen_str)
            ozone = float(ozone_str)

            if self.start_time is None:
                self.start_time = time.time()

            now = time.time() - self.start_time

            self.hydrogen_data.append(hydrogen)
            self.ozone_data.append(ozone)
            self.time_data.append(now)

        except Exception as e:
            self.get_logger().error(f"Error parsing H2/O3 data '{msg.data}': {e}")

    # --- Timer-based Methods ---

    def log_data_to_csv(self):
        """Logs the latest set of sensor data to the CSV file."""
        if self.csv_writer is None:
            return

        # Get latest data, using last item in deque or None if empty
        hydrogen_val = self.hydrogen_data[-1] if self.hydrogen_data else None
        ozone_val = self.ozone_data[-1] if self.ozone_data else None

        # Prepare data row, handling None values by writing empty strings
        row = [
            time.time(),
            self.current_geiger_data if self.current_geiger_data is not None else '',
            ozone_val if ozone_val is not None else '',
            hydrogen_val if hydrogen_val is not None else '',
            self.current_latitude if self.current_latitude is not None else '',
            self.current_longitude if self.current_longitude is not None else ''
        ]
        self.csv_writer.writerow(row)

    def update_plot(self):
        """Updates the matplotlib plot with new data from the deques."""
        current_len = len(self.hydrogen_data)
        pad_len = self.buffer_size - current_len

        h_data = list(self.hydrogen_data) + [float('nan')] * pad_len
        o_data = list(self.ozone_data) + [float('nan')] * pad_len
        t_data = list(self.time_data) + [float('nan')] * pad_len

        self.h_line.set_data(t_data, h_data)
        self.o_line.set_data(t_data, o_data)

        valid_times = [t for t in t_data if not math.isnan(t)]
        if len(valid_times) >= 2:
            self.ax1.set_xlim(valid_times[0], valid_times[-1])
        elif len(valid_times) == 1:
            self.ax1.set_xlim(valid_times[0], valid_times[0] + 1)
        else:
            self.ax1.set_xlim(0, 1)

        # --- Dynamic y-axis scaling ---
        if self.hydrogen_data:
            h_min, h_max = min(self.hydrogen_data), max(self.hydrogen_data)
            self.ax1.set_ylim(h_min - 5, h_max + 5)  # Add 5 units padding

        if self.ozone_data:
            o_min, o_max = min(self.ozone_data), max(self.ozone_data)
            self.ax2.set_ylim(o_min - 5, o_max + 5)  # Add 5 units padding

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)

        
    def destroy_node(self):
        """Custom cleanup method to close the CSV file."""
        self.get_logger().info('Shutting down node.')
        if self.csv_file and not self.csv_file.closed:
            self.csv_file.close()
            self.get_logger().info('CSV file closed successfully.')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    viewer = SensorArrayViewer()
    try:
        rclpy.spin(viewer)
    except KeyboardInterrupt:
        pass
    finally:
        # The destroy_node method will handle the file closing
        viewer.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()