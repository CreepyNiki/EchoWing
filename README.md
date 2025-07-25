# EchoWing

Bachelorarbeit von Niklas Halft
Thema: **Automatisierte Klassifikation von Vogelgesang und Vogelrufarten mittels Machine Learning**

EchoWing beschäftigt sich mit der automatisierten Klassifikation verschiedener Lautäußerungen heimischer Brutvogelarten – darunter Gesänge, Rufe, Alarmrufe, Bettelrufe und Flugrufe. Im Rahmen dieser Arbeit wurden Audiodaten der zehn häufigsten Brutvogelarten Deutschlands von der Datenbank [Xeno-canto](https://xeno-canto.org) gesammelt. Anschließend wurden diese Aufnahmen mit BirdNET nach Vogelarten klassifiziert und anschließend in dreisekündige Schnipsel zerlegt. Die passenden dreisekündigen Schnipesel einer Vogelart wurden anschließend in einem weiteren gefinetuneten Modell auf ihre Lautäußerungsart klassifiziert. Hierbei wurden aufgrund der unterschiedlichen Datenverfügbarkeit der einzelnen Vogelarten für jede Vogelart ein eigenes Modell trainiert. Die Modelle und Aufnahmen sind in diesem Projekt nicht enthalten. Diese kann man über den untenstehenden Link herunterladen.


## Setup

1. Herunterladen der Audioaufnahmen und Modelle der verschiedenen Vogelarten von **Sciebo**

**Download-Link**: https://uni-koeln.sciebo.de/s/MX1UsIKej251fgf

2. Ordnerstruktur herstellen

Die heruntergeladenen Ordner müssen in das Projektverzeichnis eingefügt werden. Die Struktur sollte wie folgt aussehen:
<img width="819" height="356" alt="Ordnerstruktur" src="https://github.com/user-attachments/assets/65eab6a3-6f2e-4150-b6a8-3a2ee5e1e584" />

### Preprocessing

1. Umbenennung der "**BIRDNAME**" Variable im .env File zum deutschen Namen der jeweiligen Vogelart zB. Blaumeise
2. Umbenennung der "**SpeciesName**" Variable im birdNETAnalyzer.py Skript zum englischen Namen der jeweiligen Vogelart zB. Eurasian Blue Tit
   
   <img width="646" height="192" alt="image" src="https://github.com/user-attachments/assets/1f62a182-7f41-4d19-bb77-08af258ae0af" />
   
3. Starten des passenden Skripts im Ordner File Extraktion zum Scrapen der Audiofiles von Xeno-canto
   
| Skript                            | Enthaltene Klassen                                 |
| --------------------------------- | -------------------------------------------------- |
| `getFiles.js`                     | `"alarmcall"`, `"beggingcall"`, `"call"`, `"song"` |
| `getFiles3classes.js`             | `"alarmcall"`, `"call"`, `"song"`  |
| `getFiles3classes_beggingcall.js` | `"beggingcall"`, `"call"`, `"song"`                |
| `getFilesFlightCall.js`           | `"alarmcall"`, `"flightcall"`, `"call"`, `"song"`  |

5. Starten des Python Skripts **birdNETAnalyzer.py** zur Identifikation der Vogelart
6. Starten des Python Skripts **shortenFilesIntoSegments** zur Segmentierung und Umwandlung der Audioaufnahmen in .wav Format

### Trainieren und Testen des Modells
1. Umbenennung der "*BIRDNAME*" Variable im .env File zur jeweiligen Vogelart
2. Auswahl der passenden Sample Rate der jeweiligen Vogelart in den Python Skripts **train.py** und **prediction.py**
<img width="589" height="211" alt="image" src="https://github.com/user-attachments/assets/bd85ec0f-ba54-4a83-af1f-bc6b3468e634" />

3. Starten des Python Skripts **train.py** zum Trainieren des Modells
4. Starten des Python Skripts **prediction.py** zum Evaluiieren des Modells -> Auswahl der passenden Evaluationsmetriken durch Auskommentieren

Ein großes Dankeschön an das Team von [BirdNET](https://github.com/birdnet-team/BirdNET-Analyzer) für die Bereitstellung ihres Modells! 🙏

Bei Fragen oder Feedback:
📧 nhalft@smail.uni-koeln.de
