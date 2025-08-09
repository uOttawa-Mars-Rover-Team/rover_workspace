import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import Float32
from sensor_msgs.msg import NavSatFix  # Import for GPS data
import matplotlib.pyplot as plt
from collections import deque
import time
import math
import os
import csv
from datetime import datetime

# Define the path for saving data, expanding the user's home directory
dataPath = os.path.expanduser("~/rover_workspace/src/ld_sensor_array/data/geiger_data")

class GeigerArrayViewer(Node):
    def __init__(self):
        super().__init__("geiger_array_viewer")

        # --- Subscriptions ---
        # Subscription for Geiger counter data
        self.geiger_subscription = self.create_subscription(
            String, "/geiger/data", self.geiger_callback, 10
        )

        # --- Data Buffers for Plotting ---
        self.buffer_size = 50
        self.geiger_data = deque(maxlen=self.buffer_size)
        self.geiger_time_data = deque(maxlen=self.buffer_size)
        self.start_time = None

        # --- Storage for Latest Data for CSV Logging ---
        self.current_geiger_data = None

        # --- Plot for Geiger Radiation Data ---
        plt.ion()
        self.fig2, self.ax3 = plt.subplots()
        self.g_line, = self.ax3.plot([], [], 'g-', label='Geiger CPS')
        self.ax3.set_ylim(0, 150)  # adjust based on expected CPS range
        self.ax3.set_xlabel("Time (s)")
        self.ax3.set_ylabel("Geiger Counter (CPS)", color='green')
        self.ax3.set_title("Live Geiger Readings")
        self.ax3.set_xticks([])
        self.ax3.legend(loc='upper left')
        plt.show(block=False)

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
            header = ['timestamp', 'geiger_cps']
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
        try:
            cps = float(msg.data)  # parse float from string message
            self.current_geiger_data = cps  # store latest CPS for CSV logging

            if self.start_time is None:
                self.start_time = time.time()

            now = time.time() - self.start_time
            self.geiger_data.append(cps)
            self.geiger_time_data.append(now)

        except Exception as e:
            self.get_logger().error(f"Error parsing Geiger data: {e}")


    # --- Timer-based Methods ---
    def log_data_to_csv(self):
        """Logs the latest set of sensor data to the CSV file."""
        if self.csv_writer is None:
            return

        # Prepare data row, handling None values by writing empty strings
        row = [
            time.time(),
            self.current_geiger_data if self.current_geiger_data is not None else '',
        ]
        self.csv_writer.writerow(row)


    def update_plot(self):
        """Updates the matplotlib plot with new data from the deques."""

        g_data = list(self.geiger_data) + [float('nan')] * (self.buffer_size - len(self.geiger_data))
        g_t_data = list(self.geiger_time_data) + [float('nan')] * (self.buffer_size - len(self.geiger_time_data))
        
        self.g_line.set_data(g_t_data, g_data)


        valid_times_g = [t for t in g_t_data if not math.isnan(t)]
        if len(valid_times_g) >= 2:
            self.ax3.set_xlim(valid_times_g[0], valid_times_g[-1])
        elif len(valid_times_g) == 1:
            self.ax3.set_xlim(valid_times_g[0], valid_times_g[0] + 1)
        else:
            self.ax3.set_xlim(0, 1)


        # --- Dynamic y-axis scaling ---
        if self.geiger_data:
            g_min, g_max = min(self.geiger_data), max(self.geiger_data)
            self.ax3.set_ylim(g_min - 5, g_max + 5)

        self.fig2.canvas.draw()
        self.fig2.canvas.flush_events()
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
    viewer = GeigerArrayViewer()
    plt.show(block=False)  # Ensure figure is displayed before spinning
    try:
        rclpy.spin(viewer)
    except KeyboardInterrupt:
        pass
    finally:
        viewer.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
