import time
import board
import neopixel
import analogio
import digitalio
import adafruit_debouncer
import asyncio

MAXANALOG = 65536
MAXCOLOR = 255
PIXELCOUNT = 500
INTERVAL = 0

PATTERNS = [
    [(255, 0, 0), (100, 0, 100), (0, 0, 255), (100, 0, 100), (0, 255, 0)],
    [(255, 0, 0), (150, 50, 0), (100, 100, 0), (50, 150, 0), (0, 255, 0), (50, 150, 0), (100, 100, 0), (150, 50, 0)]
]

class Control:
    def __init__(self):
        self.pixel = neopixel.NeoPixel(board.RX, PIXELCOUNT, brightness=0.2, auto_write=False)
        self.brightslider = analogio.AnalogIn(board.A3)

        self.rpot = analogio.AnalogIn(board.A0)
        self.gpot = analogio.AnalogIn(board.A1)
        self.bpot = analogio.AnalogIn(board.A2)
        
        self.brightness = 0.2
        self.solid = False
        self.color = (20, 20, 20)
        self.cycletimeidx = 3
        self.cycletime = 2
        self.patternidx = 0
        self.pattern = PATTERNS[self.patternidx]
        self.custompattern = []
        self.editcustom = False
        
        buttonpins = tuple(digitalio.DigitalInOut(pin) for pin in (board.TX, board.SCL, board.SDA))
        for pin in buttonpins:
            pin.direction = digitalio.Direction.INPUT
            pin.pull = digitalio.Pull.UP
        self.leftswitch = adafruit_debouncer.Debouncer(buttonpins[0])
        self.middleswitch = adafruit_debouncer.Debouncer(buttonpins[1])
        self.rightswitch = adafruit_debouncer.Debouncer(buttonpins[2])
    
    def cycleCycleTime(self):
        cycletimes = [0.5, 1, 2, 5, 10]
        self.cycletimeidx = (self.cycletimeidx + 1) % len(cycletimes)
        self.cycletime = cycletimes[self.cycletimeidx]
        
    def cyclePattern(self):
        self.patternidx = (self.patternidx + 1) % len(PATTERNS)
        self.pattern = PATTERNS[self.patternidx]



def analogToBrightness(val):
    return (0.0 + val) / MAXANALOG


def analogToColor(val):
    return int(((0.0 + val) / MAXANALOG) * MAXCOLOR)

print("Hello")



def calcColors(milliseconds, cycletime, colorlist, count):
    cycletime = int(cycletime * 1000)
    milliseconds = int(milliseconds)
    cycleoffset = milliseconds % cycletime
    stepoffset = int((len(colorlist) * cycleoffset) / cycletime)
    return [colorlist[(i + len(colorlist) - stepoffset) % len(colorlist)] for i in range(count)]

async def getButton(ctrl):
    while True:
        await asyncio.sleep(INTERVAL)
        ctrl.leftswitch.update()
        ctrl.middleswitch.update()
        ctrl.rightswitch.update()
        if ctrl.editcustom:
            if ctrl.leftswitch.fell:
                ctrl.editcustom = False
                if len(ctrl.custompattern) > 0:
                    ctrl.pattern = ctrl.custompattern
                ctrl.solid = False
                continue
            elif ctrl.middleswitch.fell:
                ctrl.custompattern.insert(0, ctrl.color)
                ctrl.custompattern = ctrl.custompattern[:PIXELCOUNT-1]
                continue
            elif ctrl.rightswitch.fell:
                for _ in range(2):
                    ctrl.custompattern.insert(0, ctrl.color)
                ctrl.custompattern = ctrl.custompattern[:PIXELCOUNT-1]
                continue
            continue
        if ctrl.leftswitch.fell:
            if not ctrl.solid:
                ctrl.solid = True
            else:
                ctrl.pixel.fill((0,0,0))
                ctrl.custompattern = []
                ctrl.editcustom = True
        if ctrl.middleswitch.fell:
            ctrl.cyclePattern()
        if ctrl.rightswitch.fell:
            ctrl.cycleCycleTime()
        

async def getColor(ctrl):
    while True:
        ctrl.color = (
            analogToColor(ctrl.rpot.value),
            analogToColor(ctrl.gpot.value),
            analogToColor(ctrl.bpot.value),
        )
        await asyncio.sleep(INTERVAL)

async def getBrightness(ctrl):
    while True:
        ctrl.brightness = (0.0 + ctrl.brightslider.value) / MAXANALOG
        await asyncio.sleep(INTERVAL)

async def setPixels(ctrl):
    while True:
        ctrl.pixel.brightness = ctrl.brightness
        if ctrl.editcustom:
            ctrl.pixel[0] = ctrl.color
            for i in range(len(ctrl.custompattern)):
                ctrl.pixel[i+1] = ctrl.custompattern[i]
        elif ctrl.solid:
            ctrl.pixel.fill(ctrl.color)
        else:
            lst = calcColors(time.monotonic_ns() / 1000000, ctrl.cycletime, ctrl.pattern, PIXELCOUNT)
            for i in range(len(lst)):
                ctrl.pixel[i] = lst[i]
        ctrl.pixel.show()
        await asyncio.sleep(INTERVAL)


async def main():
    ctrl = Control()
    pixel_task = asyncio.create_task(setPixels(ctrl))
    brightness_task = asyncio.create_task(getBrightness(ctrl))
    color_task = asyncio.create_task(getColor(ctrl))
    button_task = asyncio.create_task(getButton(ctrl))
    await asyncio.gather(pixel_task, brightness_task, color_task, button_task)

asyncio.run(main())