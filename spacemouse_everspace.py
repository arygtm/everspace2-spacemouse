"""Control Everspace 2 with a 3Dconnexion SpaceMouse by translating its axes and buttons into key presses.

Designed and tested for Everspace 2. The original Everspace may work with tweaks to key_map and AXIS_CONFIG, but is untested.
"""

import time
import math
import pyspacemouse
from pyspacemouse.types import ButtonSpec, DeviceInfo, ButtonState
from pynput.keyboard import Controller, Key

# =============================================================================
# USER SETTINGS
# Change these to match your Everspace 2 keybinds and how you like the controls to feel.
# =============================================================================

# Keys sent for each movement action. Must match your in-game keybinds.
key_map = {
    "forward": "z",
    "backward": "x",
    "left": "a",
    "right": "d",
    "up": "w",
    "down": "s",
    "roll_left": "q",
    "roll_right": "e",
    "boost": "u"
}

# Device buttons 1-10 send F1-F10; MENU and ESC are mapped below.
# Other SpaceMouse models have fewer or different buttons, so adjust these to match yours.
FUNC_KEYS = [Key.f1, Key.f2, Key.f3, Key.f4, Key.f5, Key.f6, Key.f7, Key.f8, Key.f9, Key.f10]
NAMED_BUTTON_KEYS = {"MENU": "p", "ESC": Key.esc}

# Per-axis feel:
#   sensitivity:         scales the input after the response curve
#   off:                 inputs below this are ignored (dead zone)
#   on:                  inputs above this hold the key down fully
#   duty_min / duty_max: fraction of each cycle the key is held between off and on,
#                        from gentlest to strongest push
AXIS_CONFIG = {
    "x": {"sensitivity": 1.0, "off": 0.05, "on": 0.45, "duty_min": 0.1, "duty_max": 0.9},     # strafe
    "y": {"sensitivity": 1.0, "off": 0.05, "on": 0.45, "duty_min": 0.1, "duty_max": 0.9},     # forward/back
    "z": {"sensitivity": 1.0, "off": 0.05, "on": 0.45, "duty_min": 0.1, "duty_max": 0.9},     # up/down
    "roll": {"sensitivity": 1.0, "off": 0.05, "on": 0.45, "duty_min": 0.1, "duty_max": 0.9},  # roll
}

# How hard you have to push (combined across strafe, forward/back and up/down) to trigger boost
BOOST_THRESHOLD = 0.5

# =============================================================================
# ADVANCED SETTINGS
# Not recommended to change. These are tuned to work well with Everspace 2's input handling.
# =============================================================================

# Input smoothing (0-1). Lower is smoother but laggier; higher is more responsive but jittery.
ALPHA = 0.25

# Duty cycles per second (Hz). Too high and short taps can be missed by the game;
# too low and gentle inputs feel stuttery instead of smooth.
CYCLE_FREQ = 50

# Minimum time (seconds) a button's key stays held, so quick taps still register in-game
MIN_BUTTON_ON_TIME = 0.1

# =============================================================================

keyboard = Controller()

# Track key states
keys = {key: False for key in key_map.values()}

# Track last press time for duty cycle phase
last_press_time = {key: 0 for key in key_map.values() if key != key_map["boost"]}

# Track (press time, key) per held button for minimum on-time
button_press_times = {}

# Map axis to (positive_key, negative_key)
KEY_MAP = {
    "x": (key_map["right"], key_map["left"]),
    "y": (key_map["forward"], key_map["backward"]),
    "z": (key_map["up"], key_map["down"]),
    "roll": (key_map["roll_right"], key_map["roll_left"]),
}


def curve(x, sensitivity=1.0):
    """Apply nonlinear curve with sensitivity scaling."""
    return (x * abs(x)) * sensitivity


def update_key(pos_key, neg_key, value, off_threshold, on_threshold, duty_min, duty_max):
    global keys, last_press_time
    current_time = time.time()
    cycle_period = 1.0 / CYCLE_FREQ

    if value > on_threshold:
        # Full press - hold the key down
        if not keys[pos_key]:
            keyboard.press(pos_key)
            keys[pos_key] = True
        if keys[neg_key]:
            keyboard.release(neg_key)
            keys[neg_key] = False

    elif value < -on_threshold:
        # Full press - hold the key down (negative direction)
        if not keys[neg_key]:
            keyboard.press(neg_key)
            keys[neg_key] = True
        if keys[pos_key]:
            keyboard.release(pos_key)
            keys[pos_key] = False

    elif abs(value) >= off_threshold:
        # Analog duty cycle zone - high frequency with variable duty cycle
        # Normalize value to 0-1 range within duty cycle zone
        duty_range = on_threshold - off_threshold
        normalized = (abs(value) - off_threshold) / duty_range

        # Map normalized value to duty cycle (0.0 to 1.0)
        # Lower analog input = lower duty cycle (key on briefly each cycle)
        # Higher analog input = higher duty cycle (key on longer each cycle)
        duty_cycle = duty_min + (duty_max - duty_min) * normalized
        duty_on_time = cycle_period * duty_cycle

        # Determine which key to control based on sign
        key_to_control = pos_key if value > 0 else neg_key
        other_key = neg_key if value > 0 else pos_key

        # Release the other key if pressed
        if keys[other_key]:
            keyboard.release(other_key)
            keys[other_key] = False

        # Determine if key should be on or off during this cycle
        time_in_cycle = (current_time - last_press_time[key_to_control]) % cycle_period
        should_be_on = time_in_cycle < duty_on_time

        # Update key state based on duty cycle
        if should_be_on and not keys[key_to_control]:
            keyboard.press(key_to_control)
            keys[key_to_control] = True
        elif not should_be_on and keys[key_to_control]:
            keyboard.release(key_to_control)
            keys[key_to_control] = False

        # Update press time at cycle boundaries
        if time_in_cycle < 0.001:  # Reset phase at cycle start
            last_press_time[key_to_control] = current_time

    else:
        # Below off_threshold - release all keys
        if keys[pos_key]:
            keyboard.release(pos_key)
            keys[pos_key] = False
        if keys[neg_key]:
            keyboard.release(neg_key)
            keys[neg_key] = False


def button_key(index, name):
    """Return the keyboard key for a device button, or None if it is unmapped."""
    if index < len(FUNC_KEYS):
        return FUNC_KEYS[index]
    return NAMED_BUTTON_KEYS.get(name)


def add_extra_buttons(device):
    """Extend the device's button specs with additional HID buttons pyspacemouse doesn't define."""
    additional_specs = [
        ButtonSpec(channel=3, byte=4, bit=3),  # BUTTON_11
        ButtonSpec(channel=3, byte=4, bit=4),  # BUTTON_12
        ButtonSpec(channel=3, byte=4, bit=5),  # SPACE
        ButtonSpec(channel=3, byte=4, bit=6),  # ENTER
        ButtonSpec(channel=3, byte=4, bit=7),  # DELETE
    ]
    additional_names = ["BUTTON_11", "BUTTON_12", "SPACE", "ENTER", "DELETE"]
    new_button_specs = device._info.button_specs + tuple(additional_specs)
    new_button_names = device._info.button_names + tuple(additional_names)
    device._info = DeviceInfo(
        name=device._info.name,
        vendor_id=device._info.vendor_id,
        product_id=device._info.product_id,
        led_id=device._info.led_id,
        axis_scale=device._info.axis_scale,
        mappings=device._info.mappings,
        button_specs=new_button_specs,
        button_names=new_button_names
    )
    device._state.buttons = ButtonState([0] * len(new_button_specs))


def release_all_keys():
    """Release every key this script may be holding, so nothing stays stuck on exit."""
    for key, pressed in keys.items():
        if pressed:
            keyboard.release(key)
            keys[key] = False
    for _, key in button_press_times.values():
        keyboard.release(key)
    button_press_times.clear()


def main():
    # Previous smoothed values
    prev = {"x": 0.0, "y": 0.0, "z": 0.0, "roll": 0.0}

    with pyspacemouse.open() as device:
        print(f"Connected to: {device.name}")
        print("Press Ctrl+C to stop.")

        add_extra_buttons(device)

        # Track previous button states for edge detection
        prev_buttons = [0] * len(device._info.button_names)

        while True:
            state = device.read()
            current_time = time.time()

            # Handle button presses with minimum on-time
            for i, (name, current) in enumerate(zip(device._info.button_names, state.buttons)):
                key = button_key(i, name)

                # Button press detected
                if current == 1 and prev_buttons[i] == 0:
                    print(f"Button pressed: {name}")
                    if key is not None and i not in button_press_times:
                        button_press_times[i] = (current_time, key)
                        keyboard.press(key)

                # Check if button should be released (minimum on-time has passed)
                if i in button_press_times and current == 0:
                    press_time, held_key = button_press_times[i]
                    if current_time - press_time >= MIN_BUTTON_ON_TIME:
                        keyboard.release(held_key)
                        del button_press_times[i]

                prev_buttons[i] = current

            # --- RAW INPUT ---
            raw = {
                "x": state.x,         # strafe
                "y": state.y,         # forward/back
                "z": state.z,         # up/down
                "roll": state.roll,   # roll
            }

            smoothed = {}

            for axis in raw:
                config = AXIS_CONFIG[axis]
                val = curve(raw[axis], config["sensitivity"])

                smoothed_val = ALPHA * val + (1 - ALPHA) * prev[axis]
                prev[axis] = smoothed_val
                smoothed[axis] = smoothed_val

            # --- APPLY CONTROLS ---
            # Hover (z), strafe (x), thrust (y), and roll
            for axis, (pos_key, neg_key) in KEY_MAP.items():
                config = AXIS_CONFIG[axis]
                update_key(pos_key, neg_key, smoothed[axis], config["off"], config["on"], config["duty_min"], config["duty_max"])

            # --- Boost handling ---
            norm = math.sqrt(smoothed["x"]**2 + smoothed["y"]**2 + smoothed["z"]**2)
            if norm > BOOST_THRESHOLD:
                if not keys[key_map["boost"]]:
                    keyboard.press(key_map["boost"])
                    keys[key_map["boost"]] = True
            else:
                if keys[key_map["boost"]]:
                    keyboard.release(key_map["boost"])
                    keys[key_map["boost"]] = False

            time.sleep(0.005)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        release_all_keys()
