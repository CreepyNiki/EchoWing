from models.BirdNETModels.MelSpecLayerSimple import MelSpecLayerSimple
from tensorflow.keras import Model
import h5py
import os
import numpy as np
import tensorflow as tf
import librosa
from sklearn.model_selection import train_test_split
from dotenv import load_dotenv
from tensorflow.keras.regularizers import L1L2, L2
import random

# Modul random (Shuffeling), numpy und Tensorflow wird ein Random Seed gesetzt, damit die Ergebnisse reproduzierbar sind
random.seed(42)
np.random.seed(42)
tf.random.set_seed(42)

load_dotenv()

birdName = os.getenv('birdName')
birdDir = f'../SoundFiles/{birdName}'
MODEL_PATH = '../models/BirdNETModels/audio-model.h5'  # Pfad zum geladenen BirdNET BaseModel
OUTPUT_MODEL_PATH = f'../models/trainedModels/birdnet_finetuned_callTypes_{birdName}.keras' # Pfad zum gespeicherten Modell

# Parameter
# Sampling Rate
SR = 32000
# Dauer der Audiodateien in Sekunden -> 3 Sekunden konnte nicht verwendet werden
DURATION = 4.5
# Anzahl Samples pro Audiodatei
SAMPLES = int(SR * DURATION)
# BatchSize
batchSize = 16

# Funktion mit der die Daten passend vorbereitet werden
def prepare_data(balanced=True):
    file_paths_per_class = {}
    label_names = ['alarmcall', 'call', 'song']
    # Label werden zu Indizes umgewandelt weil "sparse_categorical_crossentropy" nur mit numerischen Labels arbeiten kann
    label_to_idx = {label: idx for idx, label in enumerate(label_names)}

    # Durchlaufe alle Klassen und sammle die Dateipfade
    for label in label_names:
        # Verzeichnis für die Klasse wird gesucht
        class_dir = os.path.join(birdDir, label)
        for file in os.listdir(class_dir):
            # alle Dateien mit der Endung .wav werden gesammelt und an das Dictionary file_paths_per_class angefügt (key: label, value: Filepaths)
            if file.endswith(".wav"):
                if label not in file_paths_per_class:
                    file_paths_per_class[label] = []
                file_paths_per_class[label].append(os.path.join(class_dir, file))

    if balanced:
        # Anzahl der kleinsten Klasse ermitteln
        min_count = min(len(files) for files in file_paths_per_class.values())


        for label in label_names:
            # Shuffeln der Dateipfade für jede Klasse
            random.shuffle(file_paths_per_class[label])
            # Jede Klasse auf die minimale Anzahl kürzen
            file_paths_per_class[label] = file_paths_per_class[label][:min_count]


    file_paths = []
    labels = []
    for label in label_names:
        # Dictionary file_paths_per_class wird durchlaufen und die Dateipfade und Labels werden in die Listen file_paths und labels eingefügt
        files = file_paths_per_class[label]
        # Die Dateipfade werden in die Liste file_paths eingefügt
        file_paths.extend(files)
        # Die Labels werden in die Liste labels eingefügt, wobei das Label in den entsprechenden Index umgewandelt wird -> generiert von GitHub Copilot
        labels.extend([label_to_idx[label]] * len(files))

    # Ausgabe der Anzahl der Dateien pro Klasse -> generiert von GitHub Copilot
    print(f"Anzahl der Dateien pro Klasse: {dict((label, len(files)) for label, files in file_paths_per_class.items())}")
    return file_paths, labels, label_names

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


# Training des Modells
def build_dataset(file_paths, labels, batch_size, is_training):
    # Alle Audiodateien werden geladen und in ein numpy Array umgewandelt
    audio_data = np.array([load_audio(path) for path in file_paths], dtype=np.float32)
    # Labels werden in ein numpy Array umgewandelt
    labels = np.array(labels, dtype=np.int32)

    # Dataset wird erstellt aus den Audiodaten und Labels -> dieser Part wurde generiert von GitHub Copilot
    dataset = tf.data.Dataset.from_tensor_slices((audio_data, labels))

    if is_training:
        # Dataset wird gemischt
        dataset = dataset.shuffle(1000)
        # Dataset wird nach der einmaligen Iteration reinitialisiert
        dataset = dataset.repeat()
    # Dataset wird in Batches aufgeteilt
    dataset = dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return dataset


# Probleme beim Laden des BaseModells aufgrund der .h5 Dateiendung -> Modul hp5py verwendet -> Workaround von https://stackoverflow.com/questions/78187204/trying-to-export-teachable-machine-model-but-returning-error
f = h5py.File(MODEL_PATH, mode="r+")
model_config_string = f.attrs.get("model_config")


if model_config_string.find('"groups": 1,') != -1:
    model_config_string = model_config_string.replace('"groups": 1,', '')
f.attrs.modify('model_config', model_config_string)
f.flush()

model_config_string = f.attrs.get("model_config")

assert model_config_string.find('"groups": 1,') == -1

# Modell wird geladen -> MelSpecLayerSimple wird als benutzerdefinierte Schicht hinzugefügt, da sie im BaseModel von BirdNET verwendet wird
model = tf.keras.models.load_model(
    MODEL_PATH,
    custom_objects={"MelSpecLayerSimple": MelSpecLayerSimple}
)

# vorherige Layer des Modells einfrieren, damit sie nicht trainiert werden
for layer in model.layers:
    layer.trainable = False

# Regularizer hinzufügen
regularizer = L1L2(l1=1e-3, l2=1e-3)

# Letzte 2 Layer des Modells entfernen und durch neue Layer ersetzen
x = model.layers[-2].output
# Dropout hinzufügen -> gegen Overfitting
x = tf.keras.layers.Dropout(0.2)(x)
# Neue Dense-Schicht mit Regularizer hinzufügen
new_output = tf.keras.layers.Dense(4, activation='softmax', name='calltype_output', kernel_regularizer=regularizer, bias_regularizer=L2(1e-4), activity_regularizer=L2(1e-3))(x)
# Neues Modell durch Kombinieren des Basismodells und des neuen Dense Layers erstellt
new_model = tf.keras.Model(inputs=model.input, outputs=new_output)

# Kompilierung
new_model.compile(
    # Optimizer hinzugefügt
    # optimizer=tf.keras.optimizers.Nadam(0.001),
    optimizer=tf.keras.optimizers.Lion(learning_rate=0.0001),
    # Loss-Funktion für Mehrklassenklassifikation
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# Funktion zum Vorbereiten der Daten aufrufen
file_paths, labels, class_names = prepare_data()
# Train-Test-Split der Daten -> 80% Training, 20% Test
X_train, X_val, y_train, y_val = train_test_split(file_paths, labels, test_size=0.20, stratify=labels, random_state=42)

# Training mit verschiedenen Datensatzgrößen
selected_indices = []
# gezielte Auswahl der Trainingsdaten, um ausgewogenen Split der Klassen zu erreichen
for class_idx in np.unique(y_train):
    # Indizes aller Elemente dieser Klasse
    indices = [i for i, y in enumerate(y_train) if y == class_idx]
    # n = int(0.25 * len(indices))
    # n = int(0.5 * len(indices))
    n = int(0.75 * len(indices))
    selected_indices.extend(indices[:n])

selected_indices.sort()
X_train = [X_train[i] for i in selected_indices]
y_train = [y_train[i] for i in selected_indices]

# Ausgabe der Anzahl der Trainingsdaten pro Klasse
print(f"Anzahl der Trainingsdaten pro Klasse: {dict(zip(class_names, np.bincount(y_train)))}")


# Herausschreiben der Dateipfade der Testfiles für die spätere Prediction
with open(f'../models/test_files/{birdName}_test_files.txt', "w") as f:
    for path in X_val:
        # gesplittet durch neue Zeile
        f.write(path + "\n")

# Datensätze für das Training und die Validierung erstellen
train_ds = build_dataset(X_train, y_train, batch_size=batchSize, is_training=True)
val_ds = build_dataset(X_val, y_val, batch_size=batchSize, is_training=False)

# Anzahl der Schritte pro Epoche und Validierungsschritte berechnen
steps_per_epoch = len(X_train) // batchSize
validation_steps = len(X_val) // batchSize

print("Starte Training...")

new_model.fit(train_ds,
          validation_data=val_ds,
          epochs=20,
          steps_per_epoch=steps_per_epoch,
          validation_steps=validation_steps)


new_model.save(OUTPUT_MODEL_PATH)
print(f"Modell gespeichert unter: {OUTPUT_MODEL_PATH}")

