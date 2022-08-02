import time
import board
import neopixel
import analogio

MAXANALOG = 65536
MAXCOLOR = 255

time.sleep(3)
pixel = neopixel.NeoPixel(board.RX, 8)
pixel.fill((255, 0, 0))
brightslider = analogio.AnalogIn(board.A3)

rpot = analogio.AnalogIn(board.A0)
gpot = analogio.AnalogIn(board.A1)
bpot = analogio.AnalogIn(board.A2)


def analogToBrightness(val):
    return (0.0 + val) / MAXANALOG


def analogToColor(val):
    return int(((0.0 + val) / MAXANALOG) * MAXCOLOR)


while True:
    color = (
        analogToColor(rpot.value),
        analogToColor(gpot.value),
        analogToColor(bpot.value),
    )
    pixel.fill(color)
    percentage = (0.0 + brightslider.value) / MAXANALOG
    pixel.brightness = percentage
    print("Hello")
    print(brightslider.value)
    print(color)
    time.sleep(0.01)
