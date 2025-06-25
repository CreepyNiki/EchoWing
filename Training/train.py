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



SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

load_dotenv()

birdName = os.getenv('birdName')
birdDir = f'../SoundFiles/{birdName}'  # Enthält Unterordner je Rufart
MODEL_PATH = '../models/BirdNETModels/audio-model.h5'  # Pfad zum geladenen BirdNET SavedModel
OUTPUT_MODEL_PATH = f'../models/trainedModels/birdnet_finetuned_callTypes_{birdName}.keras'

# ⚙️ Parameter
SR = 32000
DURATION = 4.5  # Sekunden
SAMPLES = int(SR * DURATION)
batchSize = 16


# 📂 Daten vorbereiten
from collections import defaultdict
import random

def prepare_data(balanced=True):
    file_paths_per_class = defaultdict(list)
    label_names = ['alarmcall', 'beggingcall', 'call', 'song']
    label_to_idx = {label: idx for idx, label in enumerate(label_names)}

    for label in label_names:
        class_dir = os.path.join(birdDir, label)
        for file in os.listdir(class_dir):
            if file.endswith(".wav"):
                file_paths_per_class[label].append(os.path.join(class_dir, file))

    if balanced:
        # Anzahl der kleinsten Klasse ermitteln
        min_count = min(len(files) for files in file_paths_per_class.values())

        # Jede Klasse auf die minimale Anzahl kürzen (shuffle vorher)
        for label in label_names:
            random.shuffle(file_paths_per_class[label])
            file_paths_per_class[label] = file_paths_per_class[label][:min_count]

    # Zusammenfügen)
    file_paths = []
    labels = []
    for label in label_names:
        files = file_paths_per_class[label]
        file_paths.extend(files)
        labels.extend([label_to_idx[label]] * len(files))

    print(f"Anzahl der Dateien pro Klasse: {dict((label, len(files)) for label, files in file_paths_per_class.items())}")
    return file_paths, labels, label_names

# 🎧 Hilfsfunktion: Lade WAV und pad auf 3s
def load_audio(file_path, target_len=SAMPLES):
    y, _ = librosa.load(file_path, sr=SR)
    if len(y) < target_len:
        y = np.pad(y, (0, target_len - len(y)))
    else:
        y = y[:target_len]
    return y


# 📚 Dataset aus Audiodateien bauen
def build_dataset(file_paths, labels, batch_size, is_training=True):
    def generator():
        for path, label in zip(file_paths, labels):
            audio = load_audio(path)
            yield audio, label

    output_signature = (
        tf.TensorSpec(shape=(SAMPLES,), dtype=tf.float32),
        tf.TensorSpec(shape=(), dtype=tf.int32)
    )

    dataset = tf.data.Dataset.from_generator(generator, output_signature=output_signature)

    if is_training:
        dataset = dataset.shuffle(1000)
        dataset = dataset.repeat()
    dataset = dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return dataset

# https://stackoverflow.com/questions/78187204/trying-to-export-teachable-machine-model-but-returning-error
f = h5py.File(MODEL_PATH, mode="r+")
model_config_string = f.attrs.get("model_config")

if model_config_string.find('"groups": 1,') != -1:
    model_config_string = model_config_string.replace('"groups": 1,', '')
f.attrs.modify('model_config', model_config_string)
f.flush()

model_config_string = f.attrs.get("model_config")

assert model_config_string.find('"groups": 1,') == -1

model = tf.keras.models.load_model(
    MODEL_PATH,
    custom_objects={"MelSpecLayerSimple": MelSpecLayerSimple}
)

for layer in model.layers:
    layer.trainable = False

regularizer = L1L2(l1=1e-3, l2=1e-3)

x = model.layers[-2].output
x = tf.keras.layers.Dropout(0.2)(x)
new_output = tf.keras.layers.Dense(4, activation='softmax', name='calltype_output', kernel_regularizer=regularizer, bias_regularizer=L2(1e-4), activity_regularizer=L2(1e-3))(x)
new_model = tf.keras.Model(inputs=model.input, outputs=new_output)

# 🧱 Kompilieren
new_model.compile(
    # optimizer=tf.keras.optimizers.Nadam(0.001),
    optimizer=tf.keras.optimizers.Lion(learning_rate=0.0001),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# 📁 Daten laden
file_paths, labels, class_names = prepare_data()
X_train, X_val, y_train, y_val = train_test_split(file_paths, labels, test_size=0.20, stratify=labels, random_state=42)

# X_train = X_train[:int(0.25 * len(X_train))]
# y_train = y_train[:int(0.25 * len(y_train))]
# X_train = X_train[:int(0.50 * len(X_train))]
# y_train = y_train[:int(0.50 * len(y_train))]
# X_train = X_train[:int(0.75 * len(X_train))]
# y_train = y_train[:int(0.75 * len(y_train))]

with open(f'../models/test_files/{birdName}_test_files.txt', "w") as f:
    for path in X_val:
        f.write(path + "\n")

train_ds = build_dataset(X_train, y_train, batch_size=batchSize, is_training=True)
val_ds = build_dataset(X_val, y_val, batch_size=batchSize, is_training=False)

steps_per_epoch = len(X_train) // batchSize
validation_steps = len(X_val) // batchSize

print("🚀 Starte Training...")

new_model.fit(train_ds,
          validation_data=val_ds,
          epochs=20,
          steps_per_epoch=steps_per_epoch,
          validation_steps=validation_steps)

print("💾 Speichere Modell...")
new_model.save(OUTPUT_MODEL_PATH)
print(f"✅ Modell gespeichert unter: {OUTPUT_MODEL_PATH}")

