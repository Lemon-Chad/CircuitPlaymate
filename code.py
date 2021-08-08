from adafruit_circuitplayground import cp
import time
import patterns
import math
import random

sequence_timer = 0
current_sequence = ""

a_down = False
b_down = False

cp.pixels.brightness = 0.05

pads = [
    "A4",
    "A5",
    "A6",
    "A7",
    "A1",
    "A2",
    "A3",
]

pads_to_lights = {
    0: [0, 1],
    1: [],
    2: [2, 3],
    3: [4],
    4: [5, 6, 7],
    5: [8],
    6: [9]
}


def flash(color, count, delay=0.1):
    for i in range(count):
        cp.pixels.fill(color if i % 2 else (0, 0, 0))
        time.sleep(delay)


def warn():
    flash((255, 0, 0), 7)


current_pad = 0

while current_pad < len(pads):
    touched = [getattr(cp, "touch_" + pad) for pad in pads[current_pad:]]
    progress = current_pad / 6
    if touched.count(True) == 1 and touched[0] == True:
        current_pad += 1
    elif touched.count(True) > 0:
        current_pad = 0
        warn()
    for i in range(0, math.ceil(progress * 9)):
        cp.pixels[i] = patterns.rainbow[i]

cp.pixels.fill((0, 0, 0))
for i in range(10):
    cp.pixels[i] = patterns.rainbow[i]
    time.sleep(0.1)
flash((0, 255, 0), 7)


def aPressed():
    global a_down
    p = cp.button_a and not a_down
    a_down = cp.button_a
    return p


def bPressed():
    global b_down
    p = cp.button_b and not b_down
    b_down = cp.button_b
    return p


def scale_range(value, max_value=320):
    """Scale a value from 0-320 (light range) to 0-9 (NeoPixel range).
    Allows remapping light value to pixel position."""
    return round(value / max_value * 9)


def light_list(value):
    for i in range(10):
        cp.pixels[i] = value[i]


mood = 100
mood_lights = patterns.empty


def set_mood(value):
    global mood, mood_lights
    mood = min(max(0, value), 100)
    spread = scale_range(mood, 100)
    mood_lights = patterns.get_mood_colors(mood / 5 - 10)


def get_touched():
    return [getattr(cp, "touch_" + pad) for pad in pads]


def touchdex():
    touched = get_touched()
    if touched.count(True) > 2:
        return None
    if True not in touched:
        nonetimer = 0
        while True not in touched:
            if nonetimer > 50:
                return None
            touched = get_touched()
            nonetimer += 1
            time.sleep(0.01)
    return touched.index(True)


def sf(x):
    if x < 0: return 1
    if x > 15: return 1/3
    return math.cos(math.pi*x/15)/3+2/3


def simon_says():
    global mood
    score = 0
    seq = []

    light_list(patterns.simon.dim)

    # 1 = Red, A4 A5
    # 2 = Blue, A6 A7
    # 3 = Green, A1
    # 4 = Yellow, A2 A3
    key = [1, 1, 2, 2, 3, 4, 4]

    while True:
        seq.append(random.randint(1, 4))
        lose = False
        sp = sf(len(seq))

        for i in seq:
            if i == 1:
                light_list(patterns.simon.red)
                cp.play_tone(440, sp)
            elif i == 2:
                light_list(patterns.simon.blue)
                cp.play_tone(540, sp)
            elif i == 3:
                light_list(patterns.simon.green)
                cp.play_tone(640, sp)
            elif i == 4:
                light_list(patterns.simon.yellow)
                cp.play_tone(340, sp)

            light_list(patterns.simon.dim)

        for i in range(len(seq)):
            t = touchdex()
            while t is None:
                t = touchdex()
            answer = key[t]

            if answer == 1:
                light_list(patterns.simon.red)
                cp.play_tone(440, sp)
            elif answer == 2:
                light_list(patterns.simon.blue)
                cp.play_tone(540, sp)
            elif answer == 3:
                light_list(patterns.simon.green)
                cp.play_tone(640, sp)
            elif answer == 4:
                light_list(patterns.simon.yellow)
                cp.play_tone(340, sp)

            light_list(patterns.simon.dim)

            if answer != seq[i]:
                lose = True
                break

        if lose:
            warn()
            break

        score += len(seq)

    mood += math.sqrt(score)


def pet():
    # Get the starting point
    a = touchdex()
    if a is None: return

    # Wait for person to move their finger
    t = touchdex()
    while t == a:
        t = touchdex()

    b = t
    if b is None: return
    direction = (a - b) / abs(a - b)

    while True:
        c = touchdex()
        if c == b: continue
        if c is None:
            return
        if (b - c) / abs(b - c) != direction:
            break
        b = c

    start = min(a, b)
    end = max(a, b)

    for i in range(start, end + 1):
        for z in pads_to_lights[i]:
            cp.pixels[z] = (0, 255, 255)

    start_time = time.time()
    cp.start_tone(random.random() * 20)
    idletimer = 0
    last = None
    while True:
        c = touchdex()

        if idletimer > 30:
            break

        if c is None:
            break

        if last == c:
            idletimer += 1
            time.sleep(0.01)
        else:
            idletimer = 0
        last = c

        if start <= c <= end:
            continue

        break

    cp.stop_tone()
    end_time = time.time()
    set_mood(mood + (end_time - start_time) * 5)


sequence_actions = {
    "AA": simon_says,
}

while True:
    light_list(mood_lights)
    for i in range(len(current_sequence)):
        cp.pixels[i] = (0, 255, 255) if current_sequence[i] == "B" else (255, 255, 0)

    if random.randint(1, round(mood * 2) + 3) == 1:
        cp.play_tone(random.random() * 20 * (mood + 10) / 75, 1)

    sequence_timer += 3
    if (sequence_timer > 30 or len(current_sequence) == 10) and current_sequence != "":
        action = sequence_actions.get(current_sequence)
        if action is None:
            warn()
        else:
            action()
        current_sequence = ""
        reg_lights = []

    bprs = bPressed()
    if aPressed() or bprs:
        sequence_timer = 0
        current_sequence += "B" if bprs else "A"

    elif cp.tapped:
        brights = cp.pixels.brightness
        if brights <= 0.05:
            brights = 0.1
        else:
            brights -= 0.05
        cp.pixels.brightness = brights

    elif get_touched().count(True) == 1:
        pet()

    time.sleep(0.01)
    set_mood(mood - 0.025)

