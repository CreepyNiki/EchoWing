from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
import json
import os
from collections import Counter
import csv
import re

birdName = "Blaumeise"
speciesName = "Eurasian Blue Tit"
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
                output_file = os.path.join(root, f"{fileName}_result.json")
                with open(output_file, 'w') as json_file:
                    json_file.write(result_json)
                print(f"Results saved to: {output_file}")


# Methode zum Erstellen einer CSV-Datei mit der Zusammenfassung der Ergebnisse der Analyse
def createCSVFile():
    # CSV-Datei wird erstellt
    csv_file = open(os.path.join(files_dir, "data.csv"), 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    # CSV-Header
    csv_writer.writerow(['FileName', 'Common Name'])
    for root, dirs, files in os.walk(files_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                # Herausfiltern des Dateinamens ohne Endung der json-Datei
                fileName = os.path.splitext(file)[0]
                print(f"Processing file: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    # soundType extrahieren: Wort vor _[A-Z]_result
                    soundType = fileName.split('_')[-3]
                    data = json.load(json_file)
                    # Extrahieren der 'common_name' (Vogelnamen auf Englisch) aus den JSON-Daten
                    common_name = [detection["common_name"] for detection in data]
                    # GitHubCopilot prompt: how to print out the most common common-name in my detection list
                    if(len(common_name) > 0):
                        most_common = Counter(common_name).most_common(1)[0][0]
                        if(most_common == speciesName):
                            csv_writer.writerow([fileName, most_common, soundType])
                        else:
                            print(f"File: {fileName} - Most common species: {most_common} - soundType: {soundType}")



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



