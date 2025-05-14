from pydub import AudioSegment
import os
import re

def process_audio_files(files_dir):
    # Verarbeitung der MP3-Dateien
    for root, dirs, files in os.walk(files_dir):
        # Finden von allen MP3-Dateien im Verzeichnis
        for file in files:
            if file.endswith('.mp3'):
                file_path = os.path.join(root, file)
                audio = AudioSegment.from_file(file_path)
                duration = audio.duration_seconds

                # Extrahieren des ursprünglichen Dateinamens ohne Länge
                base_name = re.sub(r'\(\d+_\d+\)', '', os.path.splitext(file)[0]).strip()
                parts = base_name.split('_', 1)

                # Variable zum prüfen, ob Splits erstellt wurden
                splits_created = False

                # Wenn die Dauer über 120 Sekunden ist, in Drittel schneiden
                if duration > 120:
                    segment_length = len(audio) // 3
                    for i in range(3):
                        segment = audio[i * segment_length:(i + 1) * segment_length]
                        new_length = f"{int(segment.duration_seconds // 60)}_{int(segment.duration_seconds % 60)}"
                        new_file_name = f"{parts[0]}_{new_length}_{parts[1]}_part{i + 1}.mp3"
                        segment.export(os.path.join(root, new_file_name), format="mp3")
                        splits_created = True

                # Wenn die Dauer zwischen 80 und 120 Sekunden liegt, in Hälften schneiden
                elif 80 < duration <= 120:
                    segment_length = len(audio) // 2
                    for i in range(2):
                        segment = audio[i * segment_length:(i + 1) * segment_length]
                        new_length = f"{int(segment.duration_seconds // 60)}_{int(segment.duration_seconds % 60)}"
                        # Einfügen des Zeitstempels in den Dateinamen
                        new_file_name = f"{parts[0]}_{new_length}_{parts[1]}_half{i + 1}.mp3"
                        segment.export(os.path.join(root, new_file_name), format="mp3")
                        splits_created = True

                # Löschen der Ursprungsdatei, wenn Splits erstellt wurden
                if splits_created:
                    os.remove(file_path)

def deleteallparts(files_dir):
    # Löschen aller bestehenden Teile
    for root, dirs, files in os.walk(files_dir):
        for file in files:
            if re.search(r'_part\d+|_half\d+', file):
                os.remove(os.path.join(root, file))

# Beispielaufruf
birdName = "Blaumeise"
files_dir = f"Files/{birdName}/"
deleteallparts(files_dir)
process_audio_files(files_dir)