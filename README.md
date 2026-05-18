[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/QwFWBwI4)


## Start Virtual Enviroment (For Windows)
Open The Root-Directory (Assignment-03-...) in a Terminal and create + activate the virtual enviroment with:
'''
py -m venv venv
venv\Scripts\activate
'''
(venv) should now be displayed before your new CommandLine in the Terminal

Next install the requirements:
'''
pip install -r requirements.txt
'''

# Gather Data

### Start

Start VENV, then type
'''
py gather_data.py
'''

### Workflow
1. Type in your name
2. next select the activity you want to gather data for by typing the number in front of it
3. next select the placement of your data-gathering device
4. Now you get prompted to press "Button_1" in DIPPID to start gathering data
    - One run always starts with selecting an activity and placement, then there are 5 trials at 20Hz directly followed by 5 trials at 100Hz, when they are done you get a Message an can select your next activity/placement-Combo
    - a Countdown will give you time before the data-collection starts
    - If something goes wrong during a trial you can press "Button_2" when its done to redo the current trial
    - You can quit the programm at any time and continue later, it is only important that you do the run of activity and placement in order (e.g. **don't just delete a trial in the middle**, you can however delete the last one)
    - You can also redo a run completly if desired or start at a trial-Number of your choosing


# Fitness Trainer

### Start

Start VENV, then type
'''
py fitness_trainer.py
'''
    
### How to
1. Select your settings:
    - Press 2-6 to adjust the workout time per Activity
    - Press "F" for Fixed Time (Timer counts down continously and you earn points when doing the right)\
      Press "G" for "While doing it" Time (Timer only counts down while doing the right activity) **RECOMMENDED**
    - Press "H" if you want to hold the sensor in your hand\
      Press "P" if you want to keep the sensor in your pocket
2. Press "S" to start
3. After each Activity you can change the settings if you want