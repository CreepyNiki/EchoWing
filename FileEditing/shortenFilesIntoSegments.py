from pydub import AudioSegment
import os
import pandas as pd
import librosa
import soundfile as sf
from dotenv import load_dotenv
import glob

load_dotenv()
birdName = os.getenv('birdName')

files_dir = f"../SoundFiles/{birdName}/"

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
                audio.set_frame_rate(32000)
                audio.export(wav_file_path, format='wav')
                os.remove(file_path)
                print(f"Converted {file} to {wav_file_path}")


def generateSplitFiles(files_dir, birdName):
    df = pd.read_csv(f'{files_dir}/data.csv')
    # Erstelle eine Menge aller erlaubten Dateinamen mit .wav
    allowed_files = set(df['FileName'].astype(str) + '.wav')

    # Durchsuche alle WAV-Dateien in den Unterordnern
    for wav_file in glob.glob(os.path.join(files_dir, '*', '*.wav')):
        file_base = os.path.basename(wav_file)
        if file_base not in allowed_files:
            os.remove(wav_file)
            print(f"Deleted unused file: {wav_file}")

    # Gruppiere nach Datei, damit jede Ursprungsdatei nur einmal gelöscht wird
    grouped = df.groupby(['SoundType', 'FileName'])
    for (label, file_name), group in grouped:
        label_folder = label.replace(' ', '')

        input_file = f"{files_dir}/{label}/{file_name}.wav"
        for _, row in group.iterrows():
            output_file = f"{files_dir}/{label}/{file_name}_{row['Start Time']}_{row['End Time']}.wav"
            try:
                start = float(row['Start Time'])
                duration = float(row['End Time']) - float(row['Start Time'])
                y, sr = librosa.load(input_file, sr=32000, offset=start, duration=duration)
                sf.write(output_file, y, sr)
                print(f"Created split file: {output_file}")
            except Exception as e:
                print(f"Error processing {input_file}: {e}")
        # Ursprungsdatei erst nach allen Splits löschen
        if os.path.exists(input_file):
            os.remove(input_file)

# Beispielaufruf
mp3towav(files_dir)
generateSplitFiles(files_dir, birdName)
