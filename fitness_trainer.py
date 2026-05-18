import pyglet
from pyglet.window import key
import activity_recognizer
import os
from enum import IntEnum
from activity_recognizer import Placement

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1000
IMG_SCALE = 0.5
UPDATE_HERZ = 60

#To translate classNames to Display names
ACTIVITY_DISPLAY_NAMES = { 
    "jumping_jacks": '"Jumping Jacks"',
    "rowing":'"Rowing"',
    "lifting":'"Lifting"',
    "running":'"Running"',
    "not_sure": "Not reliably sure"
}
image_paths = {
    "jumping_jacks": ("img/jumpingjack_1.png", "img/jumpingjack_2.png"),
    "lifting": ("img/lifting_1.png", "img/lifting_2.png"),
    "rowing": ("img/rowing_1.png", "img/rowing_2.png"),
    "running": ("img/running_1.png", "img/running_2.png"),
}
modes = {
    -1 : "Nothing selected",
    0 : "Fixed Time",
    1 : "Only while doint it"
}
CONTROL_DESCRIPTION = "Press 1-6 to change the duration | 'f' or 'g' for Mode | 'h' for in hand, 'p' for in Pocket"

class ExcersiceMode(IntEnum):
    NOTHING_SELECTED = -1
    FIXED_TIME = 0              #Countdown goes down continously
    ONLY_DOING_IT_RIGHT = 1     #Countdown only goes down when doing the right excercise


class FitnessTrainer:
    def __init__(self):
        self.actReco = activity_recognizer.predictTraning()
        self.win = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.background = pyglet.shapes.Rectangle(
            0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, color=(255, 255, 255)
        )

        self.exercises = ["jumping_jacks", "lifting", "rowing", "running"]

        self.exercise = 0
        self.img_switch = False
        self.act_Counter = 0
        self.count_Down = 5
        self.start_Count_Down = False
        self.collection_Started = False

        self.round_Is_Running = False
        self.excersice_Mode = ExcersiceMode.NOTHING_SELECTED
        self.exercise_Duration = -1
        self.excercise_CountDown = self.exercise_Duration
        self.excercise_Judgment = ""
        self.points = 0

        self.sprites = self.load_sprites()

        self.display_image = self.sprites["jumping_jacks"][0]

        self.infoLabel = pyglet.text.Label(
            f"Press 2-6 for workout duration (20-60s) and 'f' or 'g' for Mode",
            font_size=30,
            width=WINDOW_WIDTH-100,
            height=WINDOW_HEIGHT/8,
            multiline=True,
            x = 50,
            y=WINDOW_HEIGHT - 250,
            color=(0, 0, 0),
            align="center"
        )

        self.activity_Label = pyglet.text.Label(
            "Activity: not recording yet",
            font_size=25,
            x=0,
            y=10,
            color=(0,0,0),
            align="left"
        )

        self.mode_label = pyglet.text.Label(
            f"Time:\nMode:\nPlacement: ",
            font_size=25,
            x=0,
            multiline=True,
            width=WINDOW_WIDTH,
            y=WINDOW_HEIGHT-50,
            color=(0,0,0),
            align="left"
        )
      
        self.win.event(self.on_draw)
        self.win.event(self.on_close)
        self.win.event(self.on_key_press)
        pyglet.clock.schedule_interval(self.count_Down_Update, 1)
        pyglet.clock.schedule_interval(self.update, 1/UPDATE_HERZ)
        
    def count_Down_Update(self, df):
        if self.start_Count_Down:
            self.background.color = (255,255,255,255)
            self.count_Down -= 1
            if self.count_Down == 0: #To start collecting before countdown finishes (so delay when using fixed time mode can be reduced)
                self.infoLabel.text = f"You have to do some {self.get_Activity_For_Current_Round()}\nCome on you can do it!"
                if not self.collection_Started:
                    self.start()
            elif self.count_Down < 0:
                self.count_Down = 5
                self.start_Count_Down = False
                self.round_Is_Running = True
            else:
                self.infoLabel.text = f"{self.get_Activity_For_Current_Round()} starts in {self.count_Down} seconds"


    def load_sprites(self):
        sprites = {}
        for key, (statImg, moveImg) in image_paths.items():
            imageStatic = pyglet.resource.image(statImg)
            imageMoving = pyglet.resource.image(moveImg)

            staticSprite = pyglet.sprite.Sprite(imageStatic,x=(WINDOW_WIDTH / 2 - imageStatic.width / (2/IMG_SCALE)),y=20)
            movingSprite = pyglet.sprite.Sprite(imageMoving,x=(WINDOW_WIDTH / 2 - imageMoving.width / (2/IMG_SCALE)),y=20)

            staticSprite.scale = IMG_SCALE
            movingSprite.scale = IMG_SCALE

            sprites[key] = (staticSprite, movingSprite)
        return sprites

    def switch_image(self, key):
        staticSprite, movingSprite = self.sprites[key]
        self.display_image = staticSprite if not self.img_switch else movingSprite
        self.img_switch = not self.img_switch

    def move_pic(self):
        self.switch_image(self.exercises[self.exercise])

    def choose_activity(self):
        if self.excercise_CountDown <= 0:
            self.round_Is_Running = False
            if self.exercise < 3:
                self.exercise += 1
                self.set_Judgement()
            else:
                self.exercise = 0
                self.excercise_Judgment = "Great Job! Want to do another round? :)"

            #self.count_Down = 20 #20sec between workouts (before activities just continued without user input, now each can be startet seperatly with different settings)
            
            self.infoLabel.text = f"{self.excercise_Judgment}\n{CONTROL_DESCRIPTION}\nIf you're happy, press 'S' to begin the next Round of {self.get_Activity_For_Current_Round()} :)"
            self.move_pic()
            self.background.color = (255,255,255,255)
            self.excercise_CountDown = self.exercise_Duration

    def set_Judgement(self):
        adjustedPoints = self.points/(self.exercise_Duration*UPDATE_HERZ)
           
        if adjustedPoints >= 0.9:
            self.excercise_Judgment = "Perfect!\n"
        elif adjustedPoints > 0.8:
            self.excercise_Judgment = "Almost Perfect!\n"
        elif adjustedPoints > 0.6:
            self.excercise_Judgment = "Great job!\n"
        elif adjustedPoints > 0.4:
            self.excercise_Judgment = "Well Done!\n"
        elif adjustedPoints > 0.1:
            self.excercise_Judgment = "Could be better\n"
        else:
            self.excercise_Judgment = "You failed\n"
        
    def update(self, dt):
        if self.collection_Started:
            current_activity = self.actReco.current_Activity #Gets updated every second (WINDOW_SECONDS*OVERLAP), but checked continously every 1/60sec here for smoother experience
            self.activity_Label.text = f"Activity: {ACTIVITY_DISPLAY_NAMES[current_activity]}"

        if not self.round_Is_Running:
            return
        self.infoLabel.text = f"You have to do some {self.get_Activity_For_Current_Round()}\nCome on, only {self.excercise_CountDown:.2f}s left!"
        
        target_activity = self.exercises[self.exercise]
        if self.excersice_Mode == ExcersiceMode.FIXED_TIME:
            self.excercise_CountDown -= dt
        if target_activity == current_activity:
            self.background.color = (85, 163, 103)
            if self.excersice_Mode == ExcersiceMode.ONLY_DOING_IT_RIGHT:
                self.excercise_CountDown -= dt
            self.points += 1
        else:
            self.background.color = (186, 76, 78)
        
        self.choose_activity()

        self.act_Counter += 1
        if (self.act_Counter >= 30): #move pic every 0.5sec
            self.act_Counter = 0
            self.move_pic()
    
    def start(self):
        self.actReco.start()
        self.collection_Started = True     
    
    def on_close(self):
        self.actReco.close()
        os._exit(0)

    def on_key_press(self, pressedKey, modifier):
        if self.round_Is_Running:
            return
        
        match pressedKey:
            case key._1:
                self.exercise_Duration = 10
            case key._2:
                self.exercise_Duration = 20
            case key._3:
                self.exercise_Duration = 30
            case key._4:
                self.exercise_Duration = 40
            case key._5:
                self.exercise_Duration = 50
            case key._6:
                self.exercise_Duration = 60
            case key.F:
                self.excersice_Mode = ExcersiceMode.FIXED_TIME
            case key.G:
                self.excersice_Mode = ExcersiceMode.ONLY_DOING_IT_RIGHT
            case key.H:
                self.actReco.placement = Placement.HAND
            case key.P:
                self.actReco.placement = Placement.POCKET

        self.mode_label.text = f"Time: {self.exercise_Duration}s\nMode: {modes[self.excersice_Mode]}\nPlacement: {self.actReco.placement.name.title()}"

        self.infoLabel.text = (
            f"{CONTROL_DESCRIPTION}\nIf you're happy, press 'S' to begin with {self.get_Activity_For_Current_Round()} :)"
            )
            
        if pressedKey == key.S and self.excersice_Mode != -1 and self.exercise_Duration != -1 and not self.round_Is_Running:
            self.excercise_CountDown = self.exercise_Duration
            self.start_Count_Down = True

    def get_Activity_For_Current_Round(self) -> str:
        return ACTIVITY_DISPLAY_NAMES[self.exercises[self.exercise]]

    def on_draw(self):
        self.win.clear()
        self.background.draw()
        self.display_image.draw()
        self.infoLabel.draw()
        self.activity_Label.draw()
        self.mode_label.draw()
    

actTrainer = FitnessTrainer()
pyglet.app.run()