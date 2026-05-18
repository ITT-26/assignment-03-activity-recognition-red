# this program recognizes activities
from enum import IntEnum
import numpy as np
import pandas as pd
from DIPPID import SensorUDP
import time
import threading
import feature_extractor

PORT = 5700
sensor = SensorUDP(PORT)
LIVE_RATE = 100

class Placement(IntEnum):
    HAND = 1
    POCKET = 2

class predictTraning():
    def __init__(self):
        self.placement = Placement.HAND #Switched to pyglet for selecting placement, before Placement(int(input("Type '1' to train with Phone in Hand\nType '2' to train with Phone in Pocket\nWhich would you like?: ")))
        #print("Choose: ",self.placement.name,"\n")
        self.trainModel = feature_extractor.trainModel() 
        print("Started Loading Model")
        self.hand_Model, self.hand_scaler, self.pocket_Model, self.pocket_scaler, self.label_Encoder = self.trainModel.get_Models()
        self.id = 0
        self.live_Data = []
        self.live_Window = []
        self.training_Started = False
        self.current_Activity = "not_sure"

    def close(self):
        sensor.disconnect()

    def start(self):
        if(self.training_Started): 
            return
        self.training_Started = True
        threading.Thread(target=self.training).start()

    def stop(self):
        self.training_Started = False
    
    def predict_Data(self, live_Data):
        print(f"Predicting for {self.placement.name}") #To test changing placement for activities
        df_window = pd.DataFrame(live_Data)
        features = self.trainModel.extract_features(df_window, LIVE_RATE)
        tdf = pd.DataFrame([{
            **features,
        }])
   
        if self.placement == Placement.HAND:
            tx = tdf[feature_extractor.feature_cols]
            tX_test = self.hand_scaler.transform(tx)
            probs = self.hand_Model.predict_proba(tX_test)
        elif self.placement == Placement.POCKET:
            tx = tdf[feature_extractor.feature_cols + feature_extractor.pocket_exclusive_feature_cols]
            tX_test = self.pocket_scaler.transform(tx)
            probs = self.pocket_Model.predict_proba(tX_test)

        predi = np.argmax(probs)
        confidence = np.max(probs)
        print(confidence)
        if confidence < 0.6:
            print("Couldn't really tell")
            self.current_Activity = "not_sure"
            return
        
        activity_name = self.label_Encoder.inverse_transform([predi])[0] #asked leChat how to get name from label_Encoder
        self.current_Activity = activity_name
        print(activity_name)


    def training(self):
        print("Start gathering live data")
   
        print(sensor.has_capability("accelerometer") and sensor.has_capability("gyroscope"))
        while self.training_Started:
            if sensor.has_capability("accelerometer") and sensor.has_capability("gyroscope"):
                if len(self.live_Window) >= LIVE_RATE * (feature_extractor.WINDOW_SECONDS*feature_extractor.OVERLAP):
                    self.live_Data[len(self.live_Window):] = self.live_Data[:len(self.live_Window)]
                    self.live_Data[:len(self.live_Window)] = self.live_Window
                    
                    if len(self.live_Data) >= LIVE_RATE * feature_extractor.WINDOW_SECONDS: #skip first pred when live_Data isnt size of windows
                        self.predict_Data(self.live_Data)

                    self.live_Window.clear()
                    self.id = 0
                    continue
                
                millisecondsSinceEpoch = int(time.time() * 1000)  
                accelerator_data = sensor.get_value("accelerometer")
                gyro_data = sensor.get_value("gyroscope")

                acc_x, acc_y, acc_z = accelerator_data["x"], accelerator_data["y"], accelerator_data["z"]
                gyro_x, gyro_y, gyro_z = gyro_data["x"], gyro_data["y"], gyro_data["z"]
                

                self.live_Window.append({
                    "id": self.id,
                    "timestamp": millisecondsSinceEpoch,
                    "acc_x": acc_x,
                    "acc_y": acc_y,
                    "acc_z": acc_z,
                    "gyro_x": gyro_x,
                    "gyro_y": gyro_y,
                    "gyro_z": gyro_z
                })
                self.id += 1
            time.sleep(1/LIVE_RATE)