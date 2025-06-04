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
                base_name = os.path.splitext(file)[0]
                match = re.match(r'(.+?)_\(\d+_\d+\)_([A-Za-z]+)_(.+)', base_name)
                if not match:
                    continue
                # Splitten des Dateinamens in Vogelnamen, Land und Rest des Filenamens
                basename, country, rest = match.groups()
                splits_created = False

                # Split in 4 Teile, wenn Dauer > 120s
                if duration > 120:
                    num_parts = 4
                # Split in 3 Drittel, wenn 80 < Dauer ≤ 120s
                elif 80 < duration <= 120:
                    num_parts = 3
                # Split in 2 Hälften, wenn 50 < Dauer ≤ 80s
                elif 50 < duration <= 80:
                    num_parts = 2
                # Keine Teilung
                else:
                    num_parts = 1

                if num_parts > 1:
                    # Audio in die entsprechenden Teile aufteilen
                    segment_length = len(audio) // num_parts
                    for i in range(num_parts):
                        segment = audio[i * segment_length:(i + 1) * segment_length]
                        # Berechnung der neuen Länge in Minuten und Sekunden
                        new_length = f"{int(segment.duration_seconds // 60)}_{int(segment.duration_seconds % 60)}"
                        # Erstellen des neuen Dateinamens
                        new_file_name = f"{basename}_{new_length}_{country}{i+1}_{rest}.mp3"
                        segment.export(os.path.join(root, new_file_name), format="mp3")
                        splits_created = True

                if splits_created:
                    os.remove(file_path)

def deleteallparts(files_dir):
    for root, dirs, files in os.walk(files_dir):
        files_set = set(files)
        for file in files:
            if file.endswith('.mp3'):
                base_name = os.path.splitext(file)[0]
                match = re.match(r'(.+?)_\(\d+_\d+\)_([A-Za-z]+)_(.+)', base_name)
                if not match:
                    continue
                basename, country, rest = match.groups()
                # Löschen der Ursprungsfiles, welche geteilt wurden -> RegEx von Deepseek generiert
                pattern = re.compile(re.escape(f"{basename}_") + r"\d+_\d+_" + re.escape(f"{country}") + r"\d+_" + re.escape(rest) + r"\.mp3")
                if any(pattern.fullmatch(f) for f in files_set):
                    os.remove(os.path.join(root, file))

# Beispielaufruf
birdName = "Blaumeise"
files_dir = f"Files/{birdName}/"
deleteallparts(files_dir)
process_audio_files(files_dir)