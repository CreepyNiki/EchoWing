import tensorflow as tf
import numpy as np
import librosa
import os
from models.BirdNETModels.MelSpecLayerSimple import MelSpecLayerSimple
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
MODEL_PATH = f'../models/trainedModels/birdnet_finetuned_callTypes_{birdName}.keras'
CLASS_NAMES = ['alarmcall', 'beggingcall', 'call', 'song']

def random_baseline(y_true):
    num_classes = len(CLASS_NAMES)
    # Generate random predictions
    y_pred_random = np.random.randint(0, num_classes, size=len(y_true))

    # Print evaluation metrics
    print(classification_report(y_true, y_pred_random, target_names=CLASS_NAMES))

def display_confusion_matrix():
    print("✅ Confusion Matrix:")
    cm = confusion_matrix(y_true, y_pred_classes)
    cm_display = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=CLASS_NAMES)
    cm_display.plot()
    plt.show()

def plot_ROC():
    print("✅ ROC Curves (One-vs-Rest):")
    # Binarize the true labels
    y_true_bin = label_binarize(y_true, classes=np.arange(len(CLASS_NAMES)))
    plt.figure(figsize=(10, 8))

    for i in range(len(CLASS_NAMES)):
        fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_pred[:, i])
        roc_auc = auc(fpr, tpr)

        plt.plot(fpr, tpr, lw=2, label=f'{CLASS_NAMES[i]} (AUC = {roc_auc:.2f})')

    # Plot the diagonal
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')

    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic - Multi-Class')
    plt.legend(loc='lower right')
    plt.grid(True)
    plt.show()

def cohens_kappa(y_true, y_pred_classes):
    cm = confusion_matrix(y_true, y_pred_classes)
    total = np.sum(cm)
    p0 = np.trace(cm) / total
    pe = np.sum(np.sum(cm, axis=0) * np.sum(cm, axis=1)) / (total ** 2)
    kappa = (p0 - pe) / (1 - pe)
    return kappa

def precision_recall_curve():
    from sklearn.metrics import precision_recall_curve
    from sklearn.metrics import average_precision_score

    y_true_bin = label_binarize(y_true, classes=np.arange(len(CLASS_NAMES)))
    plt.figure(figsize=(10, 8))

    for i in range(len(CLASS_NAMES)):
        precision, recall, _ = precision_recall_curve(y_true_bin[:, i], y_pred[:, i])
        avg_precision = average_precision_score(y_true_bin[:, i], y_pred[:, i])

        plt.plot(recall, precision, lw=2, label=f'{CLASS_NAMES[i]} (AP = {avg_precision:.2f})')

    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve - Multi-Class')
    plt.legend(loc='lower left')
    plt.grid(True)
    plt.show()


# Lade validierungspfade
with open(f'../models/test_files/{birdName}_test_files.txt', "r") as f:
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
model = tf.keras.models.load_model(
    MODEL_PATH,
    custom_objects={"MelSpecLayerSimple": MelSpecLayerSimple}
)

y_pred = model.predict(X)
y_pred_classes = np.argmax(y_pred, axis=1)

# Metriken anzeigen


print("✅ Evaluationsergebnisse:")
print(classification_report(y_true, y_pred_classes, target_names=CLASS_NAMES))
for i in range(len(y_pred_classes)):
    print(f"Vorhergesagter Wert: {CLASS_NAMES[y_pred_classes[i]]}, Wahrer Wert: {CLASS_NAMES[y_true[i]]}, Datei: {val_paths[i]}")
    if y_pred_classes[i] != y_true[i]:
        print(f"❌ Fehler bei Datei: {val_paths[i]} - Vorhergesagt: {CLASS_NAMES[y_pred_classes[i]]}, Wahrer Wert: {CLASS_NAMES[y_true[i]]}")

# random_baseline(y_true)
# display_confusion_matrix()
# plot_ROC()
# kappa = cohens_kappa(y_true, y_pred_classes)
# print("✅ Cohens Kappa:", kappa)

# precision_recall_curve()