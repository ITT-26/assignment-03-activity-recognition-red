import numpy as np
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from scipy.signal import correlate, find_peaks
from sklearn.multiclass import OneVsRestClassifier

WINDOW_SECONDS = 2 #2Seconds window proved itself as good balance between accuracy and latency for predictions
OVERLAP = 0.5
feature_cols = [
        "acc_x_mean", 
        "acc_x_std",
        "acc_y_mean", 
        "acc_y_std",
        "acc_z_mean", 
        "acc_z_std",

        "acc_x_corr",
        "acc_y_corr",
        "acc_z_corr",
        "gyro_x_corr",
        "gyro_y_corr",
        "gyro_z_corr",

        "acc_mag_mean", 
        "acc_mag_std",
        "gyro_mag_mean", 
        "gyro_mag_std",

        "acc_mag_fft",
        "gyro_mag_fft",     

        "acc_corr",
        "gyro_corr",
        "peak_count",

        #-----------------------------------------
        #FILTERED OUT BY TRIAL AND ERROR:
        #"acc_x_fft" ,"acc_y_fft" ,"acc_z_fft" ,"gyro_x_fft","gyro_y_fft","gyro_z_fft",

        #"acc_x_amp","acc_y_amp","acc_z_amp","gyro_x_amp","gyro_y_amp","gyro_z_amp",
        
        #"gyro_x_mean","gyro_x_std","gyro_y_mean","gyro_y_std","gyro_z_mean","gyro_z_std",

        #"acc_mag_amp","gyro_mag_amp",
        #"gyro_energy",
]

pocket_exclusive_feature_cols = [
    "gyro_x_mean",
    "gyro_x_std",
    "gyro_y_mean",
    "gyro_y_std",
    "gyro_z_mean",
    "gyro_z_std",

    "acc_energy",
]

name_gyro_test_set = set()
hand_scaler = StandardScaler()
pocket_scaler = StandardScaler()
minMaxScaler = MinMaxScaler()
labelEncoder = LabelEncoder()


class trainModel():
    def __init__(self):
        self.rows = []
        self.fix_Names()
        if os.path.exists("features_dataset.csv"):
            self.df = pd.read_csv("features_dataset.csv")
            required_cols = feature_cols + ["activity","person","placement"]
            missing = [col for col in required_cols if col not in self.df.columns] #leChat improved my standard for-loop
            if missing:
                print("New required cols found, generating new csv")
                self.load_Data()
            else:
                print("Cols match, loading from CSV")
        else:
            print("No feature csv, generating new")
            self.load_Data()
        #self.load_Data()

    #splits the csv-files in windows with my specified length (easier to make liveData & trainData match)
    def create_windows(self, csvFile, freqs):
        window_size = freqs * WINDOW_SECONDS #since freq are samples per second -> freq * Seconds gets elements per seconds
        step = int(window_size * OVERLAP)    # how much i(start) in the forloop has to increase each step for the specified Overlpa
        windows = []
        for start in range(0, len(csvFile) - window_size, step):
            windows.append(csvFile[start:start + window_size])
        return windows  

    def get_FFT_Dominant(self,freq, rate):
        fft = np.fft.rfft(freq * np.hanning(len(freq))) 
        fft_mag = np.abs(fft)
        freqs = np.fft.rfftfreq(len(freq), d=1/rate)

        dom_index = np.argmax(fft_mag[1:]) + 1
        dom_freq = freqs[dom_index]
        amp = fft_mag[dom_index]
        return dom_freq, amp
    
    def autocorr_peak(self, x, freq):
        x = x - np.mean(x)
        corr = correlate(x, x, mode="full")
        corr = corr[len(corr)//2:]

        #the following was added through ChatGPT before it was just: "return np.max(corr[1:])", also suggested using peaks in general
        corr = corr / (corr[0] + 1e-8)

        min_lag = int(0.2 * freq)
        max_lag = len(x) // 2
        peaks, _ = find_peaks(corr[min_lag:max_lag])

        if len(peaks) == 0:
            return 0

        return np.max(corr[min_lag:max_lag][peaks])

    def extract_features(self, window, frq,person="live", activity="" , placement="", recId = ""):
        acc_x = window["acc_x"]
        acc_y = window["acc_y"]
        acc_z = window["acc_z"]

        gyro_x = window["gyro_x"]
        gyro_y = window["gyro_y"]
        gyro_z = window["gyro_z"]

        #Not 100% reliable since even with degree/s it can be smaller, but as long as the first files are bigger => person gets added as using degree/s and subsequently all their files get converted
        if person != "live" and  person in name_gyro_test_set or max(np.max(np.abs(gyro_x)), np.max(np.abs(gyro_y)), np.max(np.abs(gyro_z))) > 50: #Magic number, could also have hardcoded it to the names
            gyro_x = gyro_x * np.pi / 180
            gyro_y = gyro_y * np.pi / 180
            gyro_z = gyro_z * np.pi / 180
            name_gyro_test_set.add(person)
        
        acc_x_fft , acc_x_amp  =  self.get_FFT_Dominant(acc_x, frq)
        acc_y_fft , acc_y_amp  =  self.get_FFT_Dominant(acc_y, frq)
        acc_z_fft , acc_z_amp  =  self.get_FFT_Dominant(acc_z, frq)
        gyro_x_fft, gyro_x_amp =  self.get_FFT_Dominant(gyro_x, frq)
        gyro_y_fft, gyro_y_amp =  self.get_FFT_Dominant(gyro_y, frq)
        gyro_z_fft, gyro_z_amp =  self.get_FFT_Dominant(gyro_z, frq)

        acc_x_corr  = self.autocorr_peak(acc_x, frq) 
        acc_y_corr  = self.autocorr_peak(acc_y, frq) 
        acc_z_corr  = self.autocorr_peak(acc_z, frq) 
        gyro_x_corr = self.autocorr_peak(gyro_x, frq)
        gyro_y_corr = self.autocorr_peak(gyro_y, frq)
        gyro_z_corr = self.autocorr_peak(gyro_z, frq)

        acc_mag = np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
        gyro_mag = np.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)

        acc_corr = self.autocorr_peak(acc_mag,frq)
        gyro_corr = self.autocorr_peak(gyro_mag,frq)

        acc_mag_fft, acc_mag_amp = self.get_FFT_Dominant(acc_mag, frq)
        gyro_mag_fft, gyro_mag_amp = self.get_FFT_Dominant(gyro_mag, frq)

        #Just extracted all feature-ideas into own csv, so i can easily compare input-features by just commenting out/in in feature_cols
        return {
            "acc_x_mean": acc_x.mean(),
            "acc_x_std": acc_x.std(),
            "acc_y_mean": acc_y.mean(),
            "acc_y_std": acc_y.std(),
            "acc_z_mean": acc_z.mean(),
            "acc_z_std": acc_z.std(),

            "acc_x_corr": acc_x_corr , 
            "acc_y_corr": acc_y_corr , 
            "acc_z_corr": acc_z_corr , 
            "gyro_x_corr": gyro_x_corr,
            "gyro_y_corr": gyro_y_corr,
            "gyro_z_corr": gyro_z_corr,


            "acc_x_fft" : acc_x_fft,
            "acc_y_fft" : acc_y_fft,
            "acc_z_fft" : acc_z_fft,
            "gyro_x_fft" : gyro_x_fft,
            "gyro_y_fft" : gyro_y_fft,
            "gyro_z_fft" : gyro_z_fft,

            "acc_x_amp": acc_x_amp,
            "acc_y_amp": acc_y_amp,
            "acc_z_amp": acc_z_amp,
            "gyro_x_amp": gyro_x_amp,
            "gyro_y_amp": gyro_y_amp,
            "gyro_z_amp": gyro_z_amp,
                        
            "gyro_x_mean": gyro_x.mean(),
            "gyro_x_std": gyro_x.std(),
            "gyro_y_mean": gyro_y.mean(),
            "gyro_y_std": gyro_y.std(),
            "gyro_z_mean": gyro_z.mean(),
            "gyro_z_std": gyro_z.std(),

            "acc_mag_mean": acc_mag.mean(),
            "acc_mag_std": acc_mag.std(),
            "gyro_mag_mean": gyro_mag.mean(),
            "gyro_mag_std": gyro_mag.std(),

            "acc_mag_fft": acc_mag_fft,
            "gyro_mag_fft": gyro_mag_fft,
            "acc_mag_amp": acc_mag_amp,
            "gyro_mag_amp": gyro_mag_amp,

            "acc_corr": acc_corr,
            "gyro_corr": gyro_corr,
            "peak_count": len(find_peaks(acc_mag)[0]), #Gpt suggestion, see autocorr_peak

            "acc_energy": np.mean(acc_mag**2),   
            "gyro_energy": np.mean(gyro_mag**2), 
        }


    def load_Data(self):
        print("Started extracting features")
        nrOfFolders = len(os.listdir("data"))
        loadingpercent = 0
        for i, name in enumerate(os.listdir("data")):
            for file in os.listdir(f"data/{name}"):
                person, activity, hz, placement, rec_id = file.split("-") #Can cause problems if fileName is wrong (see fix_Names)
                freqs = int(hz.replace("Hz", ""))

                csvFile = pd.read_csv(f"data/{name}/{file}")
            
                for window in self.create_windows(csvFile, freqs):
                    features = self.extract_features(window, freqs, person, activity , placement, rec_id)

                    self.rows.append({
                        **features,
                        "activity": activity.lower(),
                        "person": person.lower(),
                        "placement": placement.lower(),
                        "herz": freqs,
                        "rId": rec_id
                    })
            loadingpercent = (i+1)/nrOfFolders*100
            print(f"{loadingpercent:.1f}%")
        self.df = pd.DataFrame(self.rows)
        self.df.to_csv("features_dataset.csv")
    
    def get_Models(self):
        dfHand = self.df[(self.df["placement"] != "pocket")].reset_index(drop=True)
        dfPocket = self.df[(self.df["placement"] == "pocket")].reset_index(drop=True)

        hand_model, y_test_hand, pred_hand = self.train_model(dfHand,hand_scaler,"rbf","Hand")
        pocket_model, y_test_pocket, pred_pocket = self.train_model(dfPocket,pocket_scaler,"linear","Pocket")
        
        #self.show_ConfusionPlot(y_test_hand,pred_hand,y_test_pocket,pred_pocket)

        return hand_model, hand_scaler, pocket_model, pocket_scaler, labelEncoder
    
    def train_model(self, df, standardScaler, kernel, model_name):
        loc_feature_cols = feature_cols.copy()
        if model_name == "Pocket":
            loc_feature_cols += pocket_exclusive_feature_cols
        
        x = df[loc_feature_cols] 
        y = labelEncoder.fit_transform(df["activity"])

        #X_train, X_test, y_train, y_test = train_test_split(x,y,test_size=0.2,random_state=42,stratify=y)
       
        test_people  = ["marcel", "felix"] #One with rad gyro one with degree gyro (though values are normalized anyway)
        test_mask = df["person"].isin(test_people)
        train_mask = ~test_mask
        X_train = x[train_mask]
        X_test = x[test_mask]
        y_train = y[train_mask]
        y_test = y[test_mask]

        X_train = standardScaler.fit_transform(X_train)
        X_test = standardScaler.transform(X_test)
        
        model = SVC(kernel=kernel, probability=True)
        if model_name == "Hand":
           model = OneVsRestClassifier(model)

        #For testing
        #model = RandomForestClassifier(
        #    n_estimators=200,
        #    random_state=42,
        #    n_jobs=-1
        #)
        #model = OneVsOneClassifier(model)    
            
        model.fit(X_train, y_train)

        predic = self.test_Accuracy(model,y_test,X_test,model_name)
        return model, y_test, predic
    
    def test_Accuracy(self, model, y_test, x_test, placement):
        pred = model.predict(x_test)       
        print(f"Accuracy {placement}:", accuracy_score(y_test, pred))
        print(classification_report(y_test, pred))
        return pred      

    def show_ConfusionPlot(self, testHand, predHand, testPocket, predPocket):
        cm_hand = confusion_matrix(testHand, predHand)
        cm_pocket = confusion_matrix(testPocket, predPocket)

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        fig.canvas.manager.set_window_title("Confusion Matrixes")
        disp1 = ConfusionMatrixDisplay(
            confusion_matrix=cm_hand,
            display_labels=labelEncoder.classes_
        )
        disp1.plot(ax=axes[0], cmap="Blues")
        axes[0].set_title("Hand")

        disp2 = ConfusionMatrixDisplay(
            confusion_matrix=cm_pocket,
            display_labels=labelEncoder.classes_
        )
        disp2.plot(ax=axes[1], cmap="Blues")
        axes[1].set_title("Pocket")

        plt.tight_layout()
        plt.show()

    def fix_Names(self):
        for name in os.listdir("data"):
                for file in os.listdir(f"data/{name}"):
                    filecopy = file
                    elements = file.split("-")
                    changed = False

                    if "jumpingjacks" in elements:
                        file = file.replace("jumpingjacks", "jumping_jacks")
                        changed = True

                    #Hardcoded since its easier and just one case, could also have checked if element[1] is one of the activities if not add to string then check element[2], ... , when element[x] == activity, replace the added together string and replace "-" with "_"
                    if "Thu" in elements:
                        file = file.replace("Viet-Hang-Thu", "viet_hang_thu")
                        changed = True
                
                    if changed:
                        print(f"Changed {filecopy} to {file}")
                        os.rename(f"data/{name}/{filecopy}", f"data/{name}/{file}")


