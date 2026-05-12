# this program gathers sensor data

import time
from DIPPID import SensorUDP
import threading
import os

#Notes:
# - we decided to have each activity and device placement be one run, to prevent great data loss if an error occurs
# - would rather use ";" for csv but assignment says ","
# - could use pythons import csv
# - doing them all back to back really was a workout
# - I varied the exercises additionally by switching between left/right hand and doing them faster/slower

PORT = 5700
sensor = SensorUDP(PORT)
TIME_FRAME = 10
COUNTDOWN_LENGTH = 3 #maybe increase so you have time to put phone into pocket
activities = ["rowing", "jumping_jacks","running","lifting","exit"]
placements = ["pocket", "hand"]
done_trials = []

class GatherData():
    def __init__(self):  
        self.name = input("Type your Name: ").lower()
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

        if(self.activity == "exit"):
            sensor.disconnect()
            os._exit(0)

        #Set Placement
        print("Select the Placement")
        for i, act in enumerate(placements):
            print(f"{i}: {act}")
        self.placement = placements[int(input("Select the placement: "))]
        

        existc = self.checkForExisting(20) #returns true if all exercises for specified activity/placement are already done
        if existc:
            print("Already did all trials in this category ;)\nWant to redo them?")
            confirmation = input("Type the number you want to start from (0-9) for yes or 'n' for no: ")
            if(confirmation == "n"):
                print("") #For spacing in Terminal
                self.setInfo()
            elif(confirmation.isdigit()): #would need thorough testing, but worked so far for me
                if(int(confirmation) < 0 or int(confirmation) > 9):
                    print("Number was out of bounds, please enter info again!")
                    self.setInfo()
                    return
                self.trialCount = int(confirmation)
                self.inputFinished = True
                print(f"Press Button_1 to start the trial-{self.trialCount} of {self.activity} in {self.placement} with {20 if self.trialCount < 5 else 100}Hz")
        else:
            self.inputFinished = True
            print(f"Press Button_1 to start the trial-{self.trialCount} of {self.activity} in {self.placement} with {20 if self.trialCount < 5 else 100}Hz")      
    
    def countDown(self):
        for i in range(COUNTDOWN_LENGTH):
            print(COUNTDOWN_LENGTH-i)
            time.sleep(1)
        

    def loop(self):  
        self.trialRunning = True
        currentRunTime = 0
        id = 0
        rate = 20 if self.trialCount < 5 else 100

        print("Starting in")
        self.countDown()
        print(0)
        
        csv_Rows = []

        csv_header = "id,timestamp,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z\n"

        while self.isGathering:
            if currentRunTime > TIME_FRAME:
                self.isGathering = False
                print(f"Trial {self.trialCount+1} Finished! {9-self.trialCount} left")
                break
              
            millisecondsSinceEpoch = int(time.time() * 1000)  
            accelerator_data = sensor.get_value("accelerometer")
            gyro_data = sensor.get_value("gyroscope")

            acc_x, acc_y, acc_z = accelerator_data["x"], accelerator_data["y"], accelerator_data["z"]
            gyro_x, gyro_y, gyro_z = gyro_data["x"], gyro_data["y"], gyro_data["z"]

            csv_Row = f"{id},{millisecondsSinceEpoch},{acc_x},{acc_y},{acc_z},{gyro_x},{gyro_y},{gyro_z}\n"

            print(csv_Row)

            csv_Rows.append(csv_Row)
            currentRunTime += 1/rate
            id += 1
            time.sleep(1/rate)

        #your_name-activity-sample_rate-placement_number.csv
        csvName = f"data/{self.name}/{self.name}-{self.activity}-{rate}Hz-{self.placement}-{self.trialCount%5}.csv"
        
        with open(csvName, "w") as file: #overwrite if name exists to allow for redos
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
            return

        print(f"    Press Button_1 to start the next trial of {self.activity} in {self.placement} with {20 if self.trialCount < 5 else 100}Hz")
        print(f"    Press Button_2 to redo the current trial of {self.activity} in {self.placement} with {20 if self.trialCount-1 < 5 else 100}Hz")

        self.trialRunning = False

    #Really convoluted but efficent way of doing it
    def checkForExisting(self, rate) -> bool:
        os.makedirs(f"data/{self.name}", exist_ok=True)
        files = os.listdir(f"data/{self.name}")
        existCounter = 0
        for file in files:
            if f"{self.name}-{self.activity}-{rate}Hz-{self.placement}" in file:
                existCounter += 1
        print(f"{self.activity}-{rate}Hz-{self.placement} existed {existCounter} times")

        if existCounter > self.trialCount%5: #if more exist than current trialCount%5
            self.trialCount += existCounter  #add existing to trialCount
            if self.trialCount > 9:          #all done!
                return True                         
            if self.trialCount > 4:          #if trialCount larger than number of trials for 20Hz
                return self.checkForExisting(100)  #always love recursive functions                  
                #call self since now at 5 trials so next 100Hz 
                # => Check for existing of 100Hz files 
                # => if yes add to current trialcount 
                # => now trialCount definetly larger than 4 so go to next loop
                # => now existc MUST be equal to trialCount%5 so it just continous
                
        print("Set Trial to: ", self.trialCount)
        return False

    def gather(self): 
        self.isGathering = True
        threading.Thread(target=self.loop).start()

gatherClass = GatherData()

def startGathering(data):
    if(data == 1 and gatherClass.inputFinished and not gatherClass.trialRunning):
        gatherClass.gather()

def restart(data):
    if(data == 1 and gatherClass.inputFinished and not gatherClass.trialRunning and gatherClass.trialCount > 0):
        gatherClass.trialCount -= 1
        gatherClass.gather()

def printData(data):
    print(data)

sensor.register_callback("button_1", startGathering)
sensor.register_callback("button_2", restart)

   