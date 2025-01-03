import keyboard

print("Key binding enabled.")

def trigger_shift_f12():
    keyboard.press('shift')
    keyboard.press('f12')
    keyboard.release('f12')
    keyboard.release('shift')

#def trigger_super():
#    keyboard.press('super')
#    keyboard.release('super')

while True:
    event = keyboard.read_event()
    if event.event_type == keyboard.KEY_DOWN:
        if int(event.scan_code) == 202:
            trigger_shift_f12()
        #if int(event.scan_code) == 240:
        #    trigger_super()

