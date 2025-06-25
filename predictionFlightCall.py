import tensorflow as tf
import numpy as np
import librosa
import os
from models.MelSpecLayerSimple import MelSpecLayerSimple
import traceback
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize

load_dotenv()

birdName = os.getenv('birdName')

SR = 32000
SAMPLES = SR * 4.5
MODEL_PATH = f'models/birdnet_finetuned_rufarten_{birdName}.keras'
CLASS_NAMES = ['alarmcall', 'call', 'flightcall', 'song']

# Lade validierungspfade
with open(f'{birdName}_val_files.txt', "r") as f:
    val_paths = [line.strip() for line in f.readlines()]

def load_audio(file_path):
    y, _ = librosa.load(file_path, sr=SR)
    if len(y) < SAMPLES:
        pad_width = int(SAMPLES - len(y))
        y = np.pad(y, (0, pad_width))
    else:
        y = y[:int(SAMPLES)]
    return y

X = np.array([load_audio(path) for path in val_paths])
y_true = [CLASS_NAMES.index(os.path.basename(os.path.dirname(p))) for p in val_paths]
y_true = np.array(y_true)

# Modell laden
try:
    model = tf.keras.models.load_model(
        MODEL_PATH,
        custom_objects={"MelSpecLayerSimple": MelSpecLayerSimple}
    )
except Exception as e:
    with open('error_log.txt', 'w', encoding='utf-8') as f:
        traceback.print_exc(file=f)
    print("Fehler beim Laden des Modells. Details siehe error_log.txt")

y_pred = model.predict(X)
y_pred_classes = np.argmax(y_pred, axis=1)

# Metriken anzeigen
print("✅ Evaluationsergebnisse:")
print(classification_report(y_true, y_pred_classes, target_names=CLASS_NAMES))
for i in range(len(y_pred_classes)):
    print(f"Vorhergesagter Wert: {CLASS_NAMES[y_pred_classes[i]]}, Wahrer Wert: {CLASS_NAMES[y_true[i]]}, Datei: {val_paths[i]}")
    if y_pred_classes[i] != y_true[i]:
        print(f"❌ Fehler bei Datei: {val_paths[i]} - Vorhergesagt: {CLASS_NAMES[y_pred_classes[i]]}, Wahrer Wert: {CLASS_NAMES[y_true[i]]}")
