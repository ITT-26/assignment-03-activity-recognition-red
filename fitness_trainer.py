import activity_recognizer as activity
import pyglet
import time
from pyglet import window, shapes

WINDOW_HEIGHT= 720
WINDOW_WIDTH = 1280

win = window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)

background = pyglet.shapes.Rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, color=(255, 255, 255))

Y_POS = 0
X_POS_JUMP_1 = (WINDOW_WIDTH - 432/2) /2
X_POS_JUMP_2 = (WINDOW_WIDTH - 619/2) /2
X_POS_LIFT_1 = (WINDOW_WIDTH - 605/2) /2
X_POS_LIFT_2 = (WINDOW_WIDTH - 804/2) /2
X_POS_ROW_1 = (WINDOW_WIDTH - 937/2) /2
X_POS_ROW_2 = (WINDOW_WIDTH - 1777/2) /2
X_POS_RUN_1 = (WINDOW_WIDTH - 699/2) /2
X_POS_RUN_2 = (WINDOW_WIDTH - 772/2) /2

IMG_SCALE = 0.5

img_switch = 0

jumping_static = pyglet.resource.image('img/jumpingjack_1.png')
jumping_move = pyglet.resource.image('img/jumpingjack_2.png')
lifting_static = pyglet.resource.image('img/lifting_1.png')
lifting_move = pyglet.resource.image('img/lifting_2.png')
rowing_static = pyglet.resource.image('img/rowing_1.png')
rowing_move = pyglet.resource.image('img/rowing_2.png')
running_static = pyglet.resource.image('img/running_1.png')
running_move = pyglet.resource.image('img/running_2.png')

jump_1 = pyglet.sprite.Sprite(jumping_static, x=X_POS_JUMP_1, y=Y_POS)
jump_2 = pyglet.sprite.Sprite(jumping_move, x=X_POS_JUMP_2, y=Y_POS)
lift_1 = pyglet.sprite.Sprite(lifting_static, x=X_POS_LIFT_1, y=Y_POS)
lift_2 = pyglet.sprite.Sprite(lifting_move, x=X_POS_LIFT_2, y=Y_POS)
row_1 = pyglet.sprite.Sprite(rowing_static, x=X_POS_ROW_1, y=Y_POS)
row_2 = pyglet.sprite.Sprite(rowing_move, x=X_POS_ROW_2, y=Y_POS)
run_1 = pyglet.sprite.Sprite(running_static, x=X_POS_RUN_1, y=Y_POS)
run_2 = pyglet.sprite.Sprite(running_move, x=X_POS_RUN_2, y=Y_POS)

jump_1.scale = IMG_SCALE
jump_2.scale = IMG_SCALE
lift_1.scale = IMG_SCALE
lift_2.scale = IMG_SCALE
row_1.scale = IMG_SCALE
row_2.scale = IMG_SCALE
run_1.scale = IMG_SCALE
run_2.scale = IMG_SCALE

timer = 0
exercise = 0
round = 1

exercises = ["Jumping-Jacks", "Lifting", "Rowing", "Running"]

ROUNDS = 6

info = pyglet.text.Label(f"You have to do some {exercises[exercise]}. You are in round {round} out of {ROUNDS}",
                          font_name='Times New Roman',
                          font_size=30,
                          x=20, y=WINDOW_HEIGHT-50, color=(0,0,0))

def initTrainer():
    global timer
    timer = time.time()

def movePic():
    global img_switch, exercise
    if exercise == 0:
        if img_switch == 0:
            jump_1.draw()
            img_switch = 1
        else:
            jump_2.draw()
            img_switch = 0
    elif exercise == 1:
        if img_switch == 0:
            lift_1.draw()
            img_switch = 1
        else:
            lift_2.draw()
            img_switch = 0
    elif exercise == 2:
        if img_switch == 0:
            row_1.draw()
            img_switch = 1
        else:
            row_2.draw()
            img_switch = 0
    elif exercise == 3:
        if img_switch == 0:
            run_1.draw()
            img_switch = 1
        else:
            run_2.draw()
            img_switch = 0
    time.sleep(0.5)

def chooseActivity():
    global timer, exercise, round, exercises
    timeSinceStart = time.time() - timer
    if timeSinceStart >= 10:
        if round == ROUNDS:
            if exercise < 3:
                exercise += 1
            else:
                exercise = 0
                round = 0
        else:
            round += 1
        info.text = f"You have to do some {exercises[exercise]}. You are in round {round} out of {ROUNDS}"
        timer = time.time()

initTrainer()

@win.event
def on_draw():
    win.clear()
    background.draw()
    chooseActivity()
    movePic()
    info.draw()

pyglet.app.run()