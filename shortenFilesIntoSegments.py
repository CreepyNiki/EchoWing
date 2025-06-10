from pydub import AudioSegment
import os
import re
import pydub
import pandas as pd
import librosa
import soundfile as sf

def mp3towav(files_dir):
    # alle mp3-Dateien herausfiltern
    for root, dirs, files in os.walk(files_dir):
        for file in files:
            if file.endswith('.mp3'):
                file_path = os.path.join(root, file)
                audio = AudioSegment.from_file(file_path)
                # neuen Pfad zusammensetzen
                wav_file_path = os.path.splitext(file_path)[0] + '.wav'
                # Nutzen von pydub zum Konvertieren in WAV -> https://stackoverflow.com/questions/5120555/how-can-i-convert-a-wav-from-stereo-to-mono-in-python
                audio.set_channels(1)
                audio.set_frame_rate(16000)
                audio.export(wav_file_path, format='wav')
                os.remove(file_path)
                print(f"Converted {file} to {wav_file_path}")


def generateSplitFiles(files_dir, birdName):
    df = pd.read_csv(f'Files/{birdName}/data.csv')

    # Gruppiere nach Datei, damit jede Ursprungsdatei nur einmal gelöscht wird
    grouped = df.groupby(['SoundType', 'FileName'])
    for (label, file_name), group in grouped:
        label_folder = label.replace(' ', '')
        output_dir = f"Files/{birdName}/{label_folder}"
        os.makedirs(output_dir, exist_ok=True)

        input_file = f"Files/{birdName}/{label}/{file_name}.wav"
        for _, row in group.iterrows():
            output_file = f"{output_dir}/{file_name}_{row['Start Time']}_{row['End Time']}.wav"
            try:
                start = float(row['Start Time'])
                duration = float(row['End Time']) - float(row['Start Time'])
                y, sr = librosa.load(input_file, sr=16000, offset=start, duration=duration)
                sf.write(output_file, y, sr)
            except Exception as e:
                print(f"Error processing {input_file}: {e}")
        # Ursprungsdatei erst nach allen Splits löschen
        if os.path.exists(input_file):
            os.remove(input_file)

# Beispielaufruf
birdName = "Blaumeise"
files_dir = f"Files/{birdName}/"
mp3towav(files_dir)
generateSplitFiles(files_dir, birdName)
