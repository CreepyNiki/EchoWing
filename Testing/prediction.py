import tensorflow as tf
import numpy as np
import librosa
import os
from models.BirdNETModels.MelSpecLayerSimple import MelSpecLayerSimple
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay, roc_curve, auc, cohen_kappa_score, average_precision_score, precision_recall_curve
from sklearn.preprocessing import label_binarize

load_dotenv()
birdName = os.getenv('birdName')

# Sample Rate für Blaumeise, Buchfink, Mönchsgrasmücke, Rotkehlchen, Star
SR = 48000
DURATION = 3.0

# Sample Rate für Amsel, Haussperling, Kohlmeise, Zaunkönig, Zilpzalp
# SR = 32000
# DURATION = 4.5

SAMPLES = int(SR * DURATION)
MODEL_PATH = f'../models/trainedModels/birdnet_finetuned_callTypes_{birdName}.keras'

# Hier können die Klassen angepasst werden, die evaluiert werden sollen
# CLASS_NAMES = ['alarmcall', 'beggingcall', 'call', 'song']
# CLASS_NAMES = ['alarmcall', 'call', 'flightcall', 'song']
CLASS_NAMES = ['alarmcall', 'call', 'song']
# CLASS_NAMES = ['beggingcall', 'call', 'song']


# Funktion zum Erstellen der random-Baseline
def random_baseline(y_true):
    # Klassenanzahl in Variable speichern
    num_classes = len(CLASS_NAMES)
    # Random Vorhersagen generieren
    y_pred_random = np.random.randint(0, num_classes, size=len(y_true))
    # Classification Report der random Baseline
    print("Random Baseline:")
    print(classification_report(y_true, y_pred_random, target_names=CLASS_NAMES))

# Funktion zum Anzeigen der Konfusionsmatrix
def display_confusion_matrix():
    # Confusionmatrix von sklearn erstellen lassen
    cm = confusion_matrix(y_true, y_pred_classes)
    cm_display = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=CLASS_NAMES)
    cm_display.plot()
    plt.show()

# Funktion zum Plotten der ROC-Kurven
def plot_ROC():
    # Multi-Klassen in binäre Klassen umwandeln -> https://stackoverflow.com/questions/45332410/roc-for-multiclass-classification
    y_true_bin = label_binarize(y_true, classes=np.arange(len(CLASS_NAMES)))
    plt.figure(figsize=(10, 8))

    # für jede Klasse ROC-Kurve berechnen -> https://stackoverflow.com/questions/45332410/roc-for-multiclass-classification umgewandelt
    for i in range(len(CLASS_NAMES)):
        fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_pred[:, i])
        roc_auc = auc(fpr, tpr)

        plt.plot(fpr, tpr, lw=2, label=f'{CLASS_NAMES[i]} (AUC = {roc_auc:.2f})')

    # Diagonale als Referenzlinie hinzufügen
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')

    # Achsen, Titel und Legende hinzufügen
    plt.xlim([-0.05, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.legend(loc='lower right')
    plt.show()

def cohens_kappa(y_true, y_pred_classes):
    print(cohen_kappa_score(y_true, y_pred_classes))

def plot_precision_recall_curve():
    # Multi-Klassen in binäre Klassen umwandeln -> https://stackoverflow.com/questions/45332410/roc-for-multiclass-classification
    y_true_bin = label_binarize(y_true, classes=np.arange(len(CLASS_NAMES)))
    plt.figure(figsize=(10, 8))

    # für jede Klasse Precision-Recall-Kurve berechnen -> https://stackoverflow.com/questions/56090541/how-to-plot-precision-and-recall-of-multiclass-classifier
    for i in range(len(CLASS_NAMES)):
        precision, recall, _ = precision_recall_curve(y_true_bin[:, i], y_pred[:, i])
        avg_precision = average_precision_score(y_true_bin[:, i], y_pred[:, i])

        # Plot der Precision-Recall-Kurve für jede Klasse plotten
        plt.plot(recall, precision, lw=2, label=f'{CLASS_NAMES[i]} (AP = {avg_precision:.2f})')

    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend(loc='lower left')
    plt.grid(True)
    plt.show()


# Laden der Pfade der Testfiles
with open(f'../models/test_files/{birdName}_test_files.txt', "r") as f:
    val_paths = [line.strip() for line in f.readlines()]

# Funktion zum Laden und Vorverarbeiten der Audiodateien
def load_audio(file_path, target_len=SAMPLES):
    # Audiodatei laden
    y, _ = librosa.load(file_path, sr=SR)
    # Audiodatei von 3 Sekunden auf 4,5 Sekunden verlängern oder kürzen bei Bedarf
    if len(y) < target_len:
        # Wenn die Audiodatei kürzer ist, wird sie mit Nullen aufgefüllt -> Padding
        y = np.pad(y, (0, target_len - len(y)))
    else:
        # Wenn die Audiodatei länger ist, wird sie auf die gewünschte Länge gekürzt
        y = y[:target_len]
    return y

# Methode zum Berechnen des durchschnittlichen Spektrogramms pro Klasse
def getAverageSpektrogramperClass(paths, class_names):
    # Parameter für das Spektrogramm
    n_mels = 128
    # fmin -> untere Frequenzgrenze, fmax -> obere Frequenzgrenze
    fmin = 0
    fmax = SR // 2
    # vmin -> untere Grenze der Farbskala, vmax -> obere Grenze der Farbskala
    vmin = 0
    vmax = 3
    # Schrittweite der Legende
    step = 1

    average_spectrograms = {}

    for class_name in class_names:
        # Herausfiltern der Pfade der verschiedenen Klassen für die jeweilige Vogelart
        class_paths = [p for p in paths if class_name in p]
        class_spectrograms = [
            # Erstellen des MelSpecLayerSimple des BirdNET Modells -> MelSpecLayerSimple.py
            MelSpecLayerSimple(
                sample_rate=SR,
                spec_shape=(128, 256),
                frame_step=512,
                frame_length=1024,
                fmin=fmin,
                fmax=fmax,
                data_format="channels_last"
            # Laden der Audiodatei und Berechnen des Spektrogramms -> generiert von GitHub Copilot
            )(load_audio(path)[np.newaxis, :]).numpy().squeeze()
            for path in class_paths
        ]
        # Durchschnittliches Spektrogramm für die Klasse berechnen
        average_spectrograms[class_name] = np.mean(class_spectrograms, axis=0)

        # Plotten der durchschnittlichen Spektrogramme für jede Klasse
        plt.figure(figsize=(10, 4))
        # Spektrogramm anzeigen
        img = plt.imshow(average_spectrograms[class_name], aspect='auto', origin='lower', cmap='viridis', vmin=vmin, vmax=vmax)
        plt.title(f'Durchschnittliches Spektrogramm für {class_name}')
        plt.colorbar(img, ticks=np.arange(vmin, vmax + step, step), format='%+2.0f dB')
        plt.xlabel('Zeit (Frames)')
        plt.ylabel('Frequenz (Hz)')
        # y-Achse anpassen, um die Frequenzen anzuzeigen -> generiert von GitHub Copilot
        plt.yticks(
            np.linspace(0, n_mels - 1, 10),
            labels=[f"{int(hz)}" for hz in np.linspace(fmin, fmax, 10)]
        )
        plt.show()


# Numpy Array mit allen Audiodateien erstellen -> passt diese über die load_audio Funktion an
X = np.array([load_audio(path) for path in val_paths])
# Wahre Labels extrahieren
y_true = [CLASS_NAMES.index(os.path.basename(os.path.dirname(p))) for p in val_paths]
# Wahre Labels in Numpy Array umwandeln
y_true = np.array(y_true)

# Modell laden
model = tf.keras.models.load_model(
    MODEL_PATH,
    custom_objects={"MelSpecLayerSimple": MelSpecLayerSimple}
)

# Vorhersage des Modells
y_pred = model.predict(X)
y_pred_classes = np.argmax(y_pred, axis=1)

# Metriken anzeigen
print("Vorhersagen:")
print(classification_report(y_true, y_pred_classes, target_names=CLASS_NAMES))
for i in range(len(y_pred_classes)):
    # falsche Vorhersagen anzeigen
    if y_pred_classes[i] != y_true[i]:
        print(f"❌ Fehler bei Datei: {val_paths[i]} - Vorhergesagt: {CLASS_NAMES[y_pred_classes[i]]}, Wahrer Wert: {CLASS_NAMES[y_true[i]]}")

# Evaluataionsmetriken
# random_baseline(y_true)
# display_confusion_matrix()
# plot_ROC()
# cohens_kappa(y_true, y_pred_classes)
# plot_precision_recall_curve()
getAverageSpektrogramperClass(val_paths, CLASS_NAMES)