import asyncio
from evdev import InputDevice, categorize, ecodes, list_devices
from evdev import UInput

from typing import Union, Literal, Tuple

MAPPINGS = {
    'upright_r': {
        ecodes.BTN_TR: ecodes.KEY_X,
        ecodes.BTN_TR2: ecodes.KEY_Z,
        ecodes.BTN_NORTH: ecodes.KEY_UP,
        ecodes.BTN_SOUTH: ecodes.KEY_DOWN,
        ecodes.BTN_WEST: ecodes.KEY_LEFT,
        ecodes.BTN_EAST: ecodes.KEY_RIGHT
    },

    'combined': {
        ecodes.BTN_NORTH: ecodes.KEY_X,
        ecodes.BTN_EAST: ecodes.KEY_Z,
        ecodes.BTN_DPAD_DOWN: ecodes.KEY_DOWN,
        ecodes.BTN_DPAD_UP: ecodes.KEY_UP,
        ecodes.BTN_DPAD_LEFT: ecodes.KEY_LEFT,
        ecodes.BTN_DPAD_RIGHT: ecodes.KEY_RIGHT,
        ecodes.BTN_SELECT: ecodes.KEY_ESC,
        ecodes.BTN_START: ecodes.KEY_ENTER
    }

}


class AutoJoyCon:

    # Axis mappings
    AXIS_MAP_R = {
        ecodes.ABS_RX: ("LEFT", "RIGHT"),
        ecodes.ABS_RY: ("UP", "DOWN"),
    }

    AXIS_MAP_L = {
        ecodes.ABS_X: ("LEFT", "RIGHT"),
        ecodes.ABS_Y: ("UP", "DOWN")
    }

    @staticmethod
    def _axis_to_mouse(event, axis_map, deadzone=0.1, max_speed=20, invert_y=False):

        if event.code not in axis_map:
            return 0, 0
        
        val = event.value

        if val > 255 or val < -255:
            norm = val / 32767.0
        else:
            norm = (val - 128) / 127.0
        
        # Apply deadzone
        if abs(norm) < deadzone:
            norm = 0.0

        # Debug print
        neg, pos = axis_map[event.code]
        direction = neg if norm < 0 else pos
        print(f"[AXIS] {direction}: {norm:.3f}")

        # Scale to movement
        movement = int(norm * max_speed)

        dx, dy = 0, 0

        amkeys = list(axis_map.keys())

        if event.code in (amkeys[0],):
            dx = movement
        
        elif event.code in (amkeys[1],):
            dy = -movement if invert_y else movement

        return dx, dy

    @staticmethod
    def _is_joycon(
            device: InputDevice, 
            name: Union[
                    Literal['Joy-Con (R)'], 
                    Literal['Joy-Con (L)'], 
                    Literal['Nintendo Switch Combined Joy-Cons']
                ]
        ):
        caps = device.capabilities()
        device_name = device.name
        
        if ecodes.EV_KEY not in caps:
            return False
        
        if device_name != name:
            return False
        
        keys = caps[ecodes.EV_KEY]

        # Heuristic: Joy-Con has these
        return (
            ecodes.BTN_EAST in keys and   # A button
            ecodes.BTN_SOUTH in keys and  # B button
            ecodes.BTN_TR in keys         # R shoulder
        )
    
    def __init__(self):

        # Auto Detection

        devices:dict[str, Union[InputDevice, None]] = {
            'Nintendo Switch Combined Joy-Cons': None,
            'Joy-Con (R)': None, 
            'Joy-Con (L)': None
        }

        for path in list_devices():
            dev = InputDevice(path)

            for k,v in devices.items():
                if v is not None:
                    continue
                if self._is_joycon(dev, k):
                    devices[k] = dev

        self.device:Tuple[str, InputDevice] = (None, None)
        for device_name, device in devices.items():
            if device is not None:
                self.device = (device_name, device)

        pass

    async def activate(self, mapping: dict[int, int]):
        dev_name, dev = self.device

        print(f'Listening on {dev_name}, ({dev.path})')

        # capabilities = {
        #     ecodes.EV_KEY: list(mapping.values()),  # your mapped keys
        #     ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y],
        # }
        
        # Virtual Keyboard
        # ui=UInput(capabilities, name="JoyCon +Mouse")
        ui=UInput()

        thresh = 0.75

        async for event in dev.async_read_loop():

            if event.type == ecodes.EV_ABS:
                dx, dy = self._axis_to_mouse(event, self.AXIS_MAP_R)
                if (dx >= thresh):
                    ui.write(ecodes.EV_KEY, ecodes.KEY_RIGHT, 1)
                    ui.syn()
                else:
                    ui.write(ecodes.EV_KEY, ecodes.KEY_RIGHT, 0)
                    ui.syn()

                if (dx <= -thresh):
                    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFT, 1)
                    ui.syn()
                else:
                    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFT, 0)
                    ui.syn()
                
                if (dy >= thresh):
                    ui.write(ecodes.EV_KEY, ecodes.KEY_DOWN, 1)
                    ui.syn()
                else:
                    ui.write(ecodes.EV_KEY, ecodes.KEY_DOWN, 0)
                    ui.syn()
                
                if (dy <= -thresh):
                    ui.write(ecodes.EV_KEY, ecodes.KEY_UP, 1)
                    ui.syn()
                else:
                    ui.write(ecodes.EV_KEY, ecodes.KEY_UP, 0)
                    ui.syn()
                
                # if 
                #ui.write(ecodes.EV_REL, ecodes.REL_X, dx)
                #ui.write(ecodes.EV_REL, ecodes.REL_Y, dy)
                #ui.write(ecodes.EV_SYN, ecodes.SYN_REPORT, 0)
                # ui.syn()

            if event.type == ecodes.EV_KEY:

                key_event = categorize(event)

                if key_event.scancode in mapping:
                    mapped_key = mapping[key_event.scancode]

                    # Press
                    if key_event.keystate == key_event.key_down:
                        ui.write(ecodes.EV_KEY, mapped_key, 1)
                        ui.syn()

                    # Release
                    elif key_event.keystate == key_event.key_up:
                        ui.write(ecodes.EV_KEY, mapped_key, 0)
                        ui.syn()

                    