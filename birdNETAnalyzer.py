from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
import json
import os
import csv
from dotenv import load_dotenv

load_dotenv()

birdName = os.getenv('birdName')
speciesName = "European Starling"
files_dir = f"Files/{birdName}/"

species_list = []

# Species List wird geladen -> besteht aus relevantesten Brutvögeln Deutschlands
with open('species_list.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            species = line.split('_')[0]
            species_list.append(line)

# Methode zum Erstellen von JSON-Dateien mit den Ergebnissen der Analyse durch BirdNET
def createJSONFiles():
    for root, dirs, files in os.walk(files_dir):
        # Herausfiltern aller mp3-Dateien im Verzeichnis
        for file in files:
            if file.endswith('.mp3'):
                file_path = os.path.join(root, file)
                fileName = os.path.splitext(file)[0]
                if not os.path.isfile(file_path):
                    print(f"Datei nicht gefunden: {file_path}")
                    continue
                print(f"Processing file: {fileName}")

                # Nutzen des BirdNET Repos
                # übernommen von: https://joeweiss.github.io/birdnetlib/#using-birdnet-analyzer
                analyzer = Analyzer(custom_species_list=species_list)
                recording = Recording(analyzer, file_path)
                recording.analyze()

                # Speichern der Ergebnisse in einer JSON-Datei
                result = recording.detections
                result_json = json.dumps(result, indent=4)
                # Für jede mp3-Datei wird eine JSON-Datei erstellt
                output_file = os.path.join(root, f"{fileName}.json")
                with open(output_file, 'w') as json_file:
                    json_file.write(result_json)
                print(f"Results saved to: {output_file}")


# Methode zum Erstellen einer CSV-Datei mit der Zusammenfassung der Ergebnisse der Analyse
def createCSVFile():
    csv_file = open(os.path.join(files_dir, "data.csv"), 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    # CSV-Header
    csv_writer.writerow(['FileName', 'Common Name', 'Country', 'SoundType', 'Start Time', 'End Time', 'Confidence'])
    for root, dirs, files in os.walk(files_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                fileName = os.path.splitext(file)[0]
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    data = json.load(json_file)
                    # soundType extrahieren: Wort vor _[A-Z]_result
                    parts = fileName.split('_')
                    soundType = parts[-2] if len(parts) >= 3 else ""
                    country = parts[-3] if len(parts) >= 3 else ""
                    for detection in data:
                        if detection.get("common_name", "") == speciesName:
                            common_name = detection.get("common_name", "")
                            start_time = detection.get("start_time", "")
                            end_time = detection.get("end_time", "")
                            confidence = detection.get("confidence", 0)
                            csv_writer.writerow([fileName, common_name, country, soundType, start_time, end_time, confidence])

    csv_file.close()


# Löschen aller bestehenden JSON-Dateien
def deleteallJSONFiles():
    for root, dirs, files in os.walk(files_dir):
        for file in files:
            if file.endswith('.json'):
                os.remove(os.path.join(root, file))

# Löschen aller bestehenden JSON-Dateien vor der Analyse
deleteallJSONFiles()
createJSONFiles()
createCSVFile()



