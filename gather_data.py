# this program gathers sensor data

import time
from DIPPID import SensorUDP
import threading
import os

#Notes:
# - we decided to have each activity and device placement be one run, to prevent great data loss if an error occurs
# - would rather use ";" for csv but assignment says ","
# - could use pythons import csv

PORT = 5700
sensor = SensorUDP(PORT)
RATE = 20
activities = ["rowing", "jumping_jacks", "running","lifting"]
placements = ["pocket", "hand"]
done_trials = []

class GatherData():
    def __init__(self):  
        self.name = input("Type your Name: ")
        self.setInfo()
        
    def setInfo(self):
        self.isGathering = False
        self.trialCount = 0 #Switch when trialCount > 4
        self.inputFinished = False
        self.trialRunning = False

        #Set Activity
        print("Select the Activity")
        for i, act in enumerate(activities):
            print(f"{i}: {act}")
        self.activity = activities[int(input("Select the Activity: "))]

        #Set Placement
        print("Select the Placement")
        for i, act in enumerate(placements):
            print(f"{i}: {act}")
        self.placement = placements[int(input("Select the placement: "))]
        print(f"{self.name}-{self.activity}-{self.placement}")

        #Check if already done in this "run"
        if f"{self.activity}-{self.placement}" in done_trials:
            print("You already did this trial, you want to do it again?")
            confirmation = input("Type 'y' for yes and 'n' for no: ")
            if(confirmation == "n"):
                print("") #For spacing in Terminal
                self.setInfo()
            elif(confirmation == "y"):
                self.inputFinished = True
        else:
            self.inputFinished = True        
    
    def loop(self):
        self.trialRunning = True
        timestamp = 0
        id = 0
        rate = 20 if self.trialCount < 5 else 100
        csv_Rows = []

        csv_header = "id,timestamp,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z\n"

        while self.isGathering:
            if timestamp >= 10:
                self.isGathering = False
                print(f"Trial {self.trialCount+1} Finished! {9-self.trialCount} left")
                break
              
            accelerator_data = sensor.get_value("accelerometer")
            gyro_data = sensor.get_value("gyroscope")

            acc_x, acc_y, acc_z = accelerator_data["x"], accelerator_data["y"], accelerator_data["z"]
            gyro_x, gyro_y, gyro_z = gyro_data["x"], gyro_data["y"], gyro_data["z"]

            csv_Row = f"{id},{timestamp},{acc_x},{acc_y},{acc_z},{gyro_x},{gyro_y},{gyro_z}\n"

            print(csv_Row)

            csv_Rows.append(csv_Row)
            timestamp += 1/rate
            id += 1
            time.sleep(1/rate)

        #your_name-activity-sample_rate-placement_number.csv
        csvName = f"data/{self.name}-{self.activity}-{rate}Hz-{self.placement}-{self.trialCount%5}.csv"
        with open(csvName, "w") as file:
            file.write(csv_header + "".join(csv_Rows))
        print("Wrote: ",csvName)

        self.trialCount += 1
        if self.trialCount >= 10:
            done_trials.append(f"{self.activity}-{self.placement}")
            print("\n--------------------------\nFinished all trials!\n--------------------------\nYou already did in this run:")
            for trial in done_trials:
                print(trial)
            print("\n")
            self.setInfo() #set info for new run

        print(f"Press Button_1 to start the next trial of {self.activity} in {self.placement} with {20 if self.trialCount < 5 else 100}Hz")
        self.trialRunning = False

    def gather(self):
        self.isGathering = True
        threading.Thread(target=self.loop).start()

gatherClass = GatherData()

def startGathering(data):
    if(data == 1 and gatherClass.inputFinished and not gatherClass.trialRunning):
        gatherClass.gather()

def printData(data):
    print(data)

sensor.register_callback("button_1", startGathering)


   