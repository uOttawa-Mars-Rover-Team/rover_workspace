import os
import sys
import termios
import time
import tty

# This line is good practice if the library has trouble detecting the model
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
import Jetson.GPIO as GPIO

# --- Pin and Servo Configuration ---
SERVO_PIN = 32
PWM_FREQ = 50

# --- Stepping Configuration ---
STEP_DURATION_S = 0.05
SERVO_SPEED_DPS = 50.0

# --- NEW: Define base speeds for each key ---
# By default, J is CCW (positive) and K is CW (negative)
J_KEY_BASE_SPEED = 100
K_KEY_BASE_SPEED = -100

# --- Global State ---
current_estimated_angle = 0.0

# --- GPIO and PWM Setup (moved into main for cleaner startup) ---
# We will initialize these inside the main function to ensure a clean state.
pwm = None


# --- Servo Control Function ---
def set_servo_speed(speed_percent):
    """Controls the continuous servo speed using a -100 to 100 scale."""
    global pwm
    if speed_percent < -100 or speed_percent > 100:
        print("Speed must be between -100 and 100")
        return
    duty_cycle = 7.5 + (speed_percent * 2.5 / 100)
    pwm.ChangeDutyCycle(duty_cycle)


# --- Helper function for keyboard input ---
def getch():
    """Gets a single character from stdin, without needing to press Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


# --- Function to Perform One Step ---
def move_step(speed_percent):
    """Starts the servo, waits for STEP_DURATION_S, then stops it."""
    global current_estimated_angle
    set_servo_speed(speed_percent)
    time.sleep(STEP_DURATION_S)
    set_servo_speed(0)
    angle_change = SERVO_SPEED_DPS * (speed_percent / 100.0) * STEP_DURATION_S
    current_estimated_angle += angle_change


# --- Main Program ---
def main():
    global pwm

    # --- NEW: State variable for toggling direction ---
    direction_multiplier = 1  # 1 for normal, -1 for inverted

    # Encapsulate GPIO setup in the main function's try/finally block
    try:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        pwm = GPIO.PWM(SERVO_PIN, PWM_FREQ)
        pwm.start(7.5)  # Start with servo stopped

        # --- NEW: Updated instructions for the user ---
        print("Servo Stepper Control Initialized.")
        print(f"Each key press moves the servo for {STEP_DURATION_S} seconds.")
        print("Press 'j' or 'k' to step.")
        print("Press 'b' to toggle/swap the direction of the 'j' and 'k' keys.")
        print("Press 'q' to quit.")

        while True:
            # --- NEW: Dynamic status line showing current key mappings ---
            j_dir_str = "CCW" if (J_KEY_BASE_SPEED * direction_multiplier) > 0 else "CW"
            k_dir_str = "CCW" if (K_KEY_BASE_SPEED * direction_multiplier) > 0 else "CW"

            print(
                f"\rAngle: {current_estimated_angle:.2f}° | J -> {j_dir_str}, K -> {k_dir_str} | Press a key... ",
                end="",
                flush=True,
            )

            char = getch()

            if char in "jJ":
                # Apply the multiplier to the base speed
                move_step(J_KEY_BASE_SPEED * direction_multiplier)

            elif char in "kK":
                # Apply the multiplier to the base speed
                move_step(K_KEY_BASE_SPEED * direction_multiplier)

            # --- NEW: Handle the 'b' key to toggle the direction ---
            elif char in "bB":
                direction_multiplier *= -1  # Flip the multiplier
                # Provide immediate feedback to the user
                print(
                    "\rDirection controls have been swapped!                     ",
                    end="",
                )
                time.sleep(1)  # Pause for a moment so the user can see the message

            elif char in "qQ":
                print("\nExiting program.")
                break

            else:  # Ignore other keys
                pass

    except KeyboardInterrupt:
        print("\nCaught KeyboardInterrupt. Cleaning up.")

    finally:
        print("\nFinal cleanup...")
        if pwm:  # Only run cleanup if pwm was successfully created
            set_servo_speed(0)
            time.sleep(0.5)
            pwm.stop()
        GPIO.cleanup()
        print(f"Final Estimated Angle: {current_estimated_angle:.2f}°")
        print("GPIO cleanup complete. Done.")


if __name__ == "__main__":
    main()
