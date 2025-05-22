from pydub import AudioSegment
import os
import re

# Funktion zum Teilen von Audiodateien
def process_audio_files(files_dir):
    for root, dirs, files in os.walk(files_dir):
        # alle mp3-Dateien im Verzeichnis und Unterverzeichnissen finden
        for file in files:
            if file.endswith('.mp3'):
                file_path = os.path.join(root, file)
                audio = AudioSegment.from_file(file_path)
                duration = audio.duration_seconds

                # Dateinamen herausfiltern -> RegEx von Deepseek generiert
                base_name = re.sub(r'\(\d+_\d+\)', '', os.path.splitext(file)[0]).strip()
                parts = base_name.split('_', 1)
                splits_created = False

                # Split in 4 Teile, wenn Dauer > 120s
                if duration > 120:
                    num_parts = 4
                    label = "quarter"
                # Split in 3 Drittel, wenn 80 < Dauer ≤ 120s
                elif 80 < duration <= 120:
                    num_parts = 3
                    label = "third"
                # Split in 2 Hälften, wenn 50 < Dauer ≤ 80s
                elif 50 < duration <= 80:
                    num_parts = 2
                    label = "half"
                else:
                    num_parts = 1  # Keine Teilung

                if num_parts > 1:
                    # Audio in die entsprechenden Teile aufteilen
                    segment_length = len(audio) // num_parts
                    for i in range(num_parts):
                        segment = audio[i * segment_length:(i + 1) * segment_length]
                        # Berechnung der neuen Länge in Minuten und Sekunden
                        new_length = f"{int(segment.duration_seconds // 60)}_{int(segment.duration_seconds % 60)}"
                        # Erstellen des neuen Dateinamens
                        new_file_name = f"{parts[0]}_{new_length}_{parts[1]}_{label}{i + 1}.mp3"
                        segment.export(os.path.join(root, new_file_name), format="mp3")
                        splits_created = True

                if splits_created:
                    os.remove(file_path)

def deleteallparts(files_dir):
    for root, dirs, files in os.walk(files_dir):
        for file in files:
            # Löschen der Ursprungsfiles, welche geteilt wurden -> RegEx von Deepseek generiert
            if re.search(r'_quarter\d+|_third\d+|_half\d+', file):
                os.remove(os.path.join(root, file))

# Beispielaufruf
birdName = "Blaumeise"
files_dir = f"Files/{birdName}/"
deleteallparts(files_dir)
process_audio_files(files_dir)