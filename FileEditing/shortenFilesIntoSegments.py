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
                # Sample Rate für Blaumeise, Buchfink, Mönchsgrasmücke, Rotkehlchen, Star
                y, sr = librosa.load(file_path, sr=48000)
                # Sample Rate für Amsel, Haussperling, Kohlmeise, Zaunkönig, Zilpzalp
                # y, sr = librosa.load(file_path, sr=32000)
                # neuen Pfad zusammensetzen
                wav_file_path = os.path.splitext(file_path)[0] + '.wav'
                # Umwandlung von mp3 zu wav
                sf.write(str(wav_file_path), y, sr)
                # Original mp3-Datei löschen
                os.remove(file_path)
                print(f"Converted {file} to {wav_file_path}")


def generateSplitFiles(files_dir, birdName):
    df = pd.read_csv(f'{files_dir}/data.csv')
    # Erstelle eine Menge aller erlaubten Dateinamen mit .wav
    allowed_files = set(df['FileName'].astype(str) + '.wav')

    # Durchsuche alle WAV-Dateien in den Unterordnern mit glob -> angepasster Code von: https://stackoverflow.com/questions/3964681/find-all-files-in-a-directory-with-extension-txt-in-python
    for wav_file in glob.glob(os.path.join(files_dir, '*', '*.wav')):
        file_base = os.path.basename(wav_file)
        # Files bei denen die häufigste Vogelart nicht der aktuellen entspricht werden gelöscht
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
                # Sample Rate für Blaumeise, Buchfink, Mönchsgrasmücke, Rotkehlchen, Star
                y, sr = librosa.load(input_file, sr=48000, offset=start, duration=duration)
                # Sample Rate für Amsel, Haussperling, Kohlmeise, Zaunkönig, Zilpzalp
                # y, sr = librosa.load(input_file, sr=32000, offset=start, duration=duration)
                sf.write(str(output_file), y, sr)
                print(f"Created split file: {output_file}")
            except Exception as e:
                print(f"Error processing {input_file}: {e}")
        # Ursprungsdatei erst nach allen Splits löschen
        if os.path.exists(input_file):
            os.remove(input_file)

# Beispielaufruf
mp3towav(files_dir)
generateSplitFiles(files_dir, birdName)
