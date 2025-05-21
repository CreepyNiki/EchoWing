from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
import json
import os
from collections import Counter
import csv

birdName = "Blaumeise"
speciesName = "Eurasian Blue Tit"
files_dir = f"Files/{birdName}/"

species_list = []
with open('species_list.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            species = line.split('_')[0]
            species_list.append(line)

def createJSONFiles():
    for root, dirs, files in os.walk(files_dir):

        for file in files:
            if file.endswith('.mp3'):
                file_path = os.path.join(root, file)
                fileName = os.path.splitext(file)[0]
                print(f"Processing file: {fileName}")

                # https://joeweiss.github.io/birdnetlib/#using-birdnet-analyzer
                analyzer = Analyzer(custom_species_list=species_list)
                recording = Recording(analyzer, file_path)
                recording.analyze()

                result = recording.detections
                result_json = json.dumps(result, indent=4)
                output_file = os.path.join(root, f"{fileName}_result.json")
                with open(output_file, 'w') as json_file:
                    json_file.write(result_json)
                print(f"Results saved to: {output_file}")


def createCSVFile():
    csv_file = open('data.csv', 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['FileName', 'Common Name'])
    for root, dirs, files in os.walk(files_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                fileName = os.path.splitext(file)[0]
                print(f"Processing file: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    data = json.load(json_file)
                    common_name = [detection["common_name"] for detection in data]
                    # GitHubCopilot prompt: how to print out the most common common-name in my detection list
                    if(len(common_name) > 0):
                        most_common = Counter(common_name).most_common(1)[0][0]
                        if(most_common == speciesName):
                            csv_writer.writerow([fileName, most_common])
                        else:
                            print(f"File: {fileName} - Most common species: {most_common}")




def deleteallJSONFiles():
    # Löschen aller bestehenden Teile
    for root, dirs, files in os.walk(files_dir):
        for file in files:
            if file.endswith('.json'):
                os.remove(os.path.join(root, file))


deleteallJSONFiles()
createJSONFiles()
createCSVFile()



