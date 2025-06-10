import tensorflow as tf
from models.MelSpecLayerSimple import MelSpecLayerSimple

import h5py

# https://stackoverflow.com/questions/78187204/trying-to-export-teachable-machine-model-but-returning-error
f = h5py.File("models/audio-model.h5", mode="r+")
model_config_string = f.attrs.get("model_config")

if model_config_string.find('"groups": 1,') != -1:
    model_config_string = model_config_string.replace('"groups": 1,', '')
f.attrs.modify('model_config', model_config_string)
f.flush()

model_config_string = f.attrs.get("model_config")

assert model_config_string.find('"groups": 1,') == -1

model = tf.keras.models.load_model(
    "models/audio-model.h5",
    custom_objects={"MelSpecLayerSimple": MelSpecLayerSimple}
)

print(model)