# Everspace 2 SpaceMouse Controls

Fly in [Everspace 2](https://everspace.game/) with a 3Dconnexion SpaceMouse. The script reads the SpaceMouse's axes and buttons and turns them into keyboard presses the game understands.

The SpaceMouse is a 6DOF input device that can be moved linearly along XYZ, and rotated about yaw+pitch+roll. This script maps your ship's linear movement, boost, and roll onto the SpaceMouse while keeping yaw and pitch on the mouse.

<img width="603" height="663" alt="SpaceMouseEnterpriseOverview" src="https://github.com/user-attachments/assets/87ead929-05a2-41fe-a32c-a15187ec4803" />


Everspace 2 only accepts keyboard input for these actions, so the analog feel comes from *duty cycling*: a small push on the SpaceMouse taps a key rapidly for short bursts, and a bigger push holds it down longer. Past a threshold the key is simply held and past the larger boost threshold, you will begin boosting in the direction the SpaceMouse is held.

> **Game version:** designed and tested for **Everspace 2**. It will likely work with the original Everspace after a few tweaks to the keybinds and tuning, but that hasn't been tested and isn't guaranteed.

> **SpaceMouse model:** designed for the [SpaceMouse Enterprise](https://3dconnexion.com/us/product/spacemouse-enterprise/). Other SpaceMouse models will likely work with a few tweaks, mostly to the button mappings, since they have fewer or different buttons.

## Demo: Racing in Prescott Starbase

The top-right corner shows the SpaceMouse (left hand) and regular mouse (right hand) inputs.



https://github.com/user-attachments/assets/57e9e80a-e343-4658-ba87-8a82415aa8d4



## Requirements

- macOS (tested on macOS 15 with Python 3.14)
- A 3Dconnexion SpaceMouse (designed for the [SpaceMouse Enterprise](https://3dconnexion.com/us/product/spacemouse-enterprise/))
- Python 3.9+
- [hidapi](https://github.com/libusb/hidapi): `brew install hidapi`

## Setup

```bash
git clone https://github.com/arygtm/everspace2-spacemouse.git
cd everspace2-spacemouse
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### macOS permissions

The script sends key presses through `pynput`, which macOS blocks until you allow it. Open **System Settings → Privacy & Security** and add your terminal app (Terminal, iTerm, VS Code, …) under **Accessibility**. If the SpaceMouse isn't read, also add it under **Input Monitoring**. Restart the terminal afterwards.

If the 3Dconnexion driver (3DxWare) is running, it may take over the device. Quit it before starting the script. Be sure to quit any 3Dconnexion helpers as well via Activity Monitor/Task Manager. 

## Usage

```bash
cd everspace2-spacemouse
source .venv/bin/activate
python spacemouse_everspace.py
```

Then switch to Everspace 2. Press **Ctrl+C** in the terminal to stop; any keys still held are released.

## Controls

Set these keybinds in Everspace 2 (or edit `key_map` in the script to match your existing binds).

| SpaceMouse input | Key | Everspace 2 action |
|---|---|---|
| Push forward / pull back | `Z` / `X` | Thrust forward / backward |
| Push left / right | `A` / `D` | Strafe left / right |
| Lift up / press down | `W` / `S` | Move up / down |
| Twist (roll) left / right | `Q` / `E` | Roll left / right |
| Strong push in any direction | `U` | Boost |
| Buttons 1–10 | `F1`–`F10` | Bind to whatever you like (I run devices in F1-F4 and consumables in F7-F10) |
| MENU button | `P` | |
| ESC button | `Esc` | Pause menu |

## Tuning

All the settings are constants at the top of `spacemouse_everspace.py`.

- **`AXIS_CONFIG`**: per-axis settings.
  - `sensitivity`: scales the input after the response curve.
  - `off`: inputs below this are ignored (dead zone).
  - `on`: inputs above this hold the key down fully.
  - `duty_min` / `duty_max`: between `off` and `on`, the fraction of each cycle the key is held, from gentlest to strongest push.
- **`BOOST_THRESHOLD`**: how hard you have to push (combined across all movement axes) to trigger boost.
- **`ALPHA`**: input smoothing. Lower is smoother but laggier.
- **`CYCLE_FREQ`**: how many duty cycles run per second.
- **`MIN_BUTTON_ON_TIME`**: minimum time a button's key stays held, so quick taps still register in-game.

## Acknowledgements

Built on [PySpaceMouse](https://github.com/JakubAndrysek/PySpaceMouse) and [pynput](https://github.com/moses-palmer/pynput).

## License

[MIT](LICENSE)
