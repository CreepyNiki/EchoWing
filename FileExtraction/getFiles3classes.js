const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: require('path').join(__dirname, '..', '.env') });
// Abrufen des Vogelnamens aus der .env Datei
const birdName = process.env.birdName;

// Zusammensetzen der URL für die Abfrage auf xeno-canto
const targetUrl = 'https://xeno-canto.org/explore?query=' + encodeURIComponent(birdName);
console.log(targetUrl);
const downloadDir = path.join(__dirname, '../SoundFiles', birdName);

// Cleanup der alten Ordnerstruktur
if (fs.existsSync(downloadDir)) {
    fs.rmSync(downloadDir, { recursive: true, force: true });
}

// Erstellen des neuen Folders
fs.mkdirSync(downloadDir);

// Funktion zum erneuten Abrufen nach 5 Sekunden von Daten, falls 503 Fehler auftritt
async function fetchWithRetry(url, options = {}, retries = 3, delay = 5000) {
    // Schleife, die checkt, wie viele Retries schon durchgeführt wurden
    for (let i = 0; i < retries; i++) {
        try {
            return await axios.get(url, options);
        } catch (error) {
            // Wenn ein 503 Fehler auftritt, wird nach einer Verzögerung erneut versucht und ein Retry durchgeführt
            if (error.response && error.response.status === 503 && i < retries - 1) {
                console.warn(`503 erhalten, versuche erneut in 5 Sekunden...`);
                // Timeout wird gesetzt und Promise wird abgewartet
                await new Promise(res => setTimeout(res, delay));
            } else {
                throw error;
            }
        }
    }
}

/* Funktion zur Datenextraktion von der Seite xeno-canto
 maxAmount ist die maximale Anzahl an Einträgen pro Rufartentyp
 startPage ist die Startseite der Iteration, falls mehrere Vögel einen ähnlichen Namen haben und nicht brauchbar auf xeno-canto gefiltert sind
*/

async function getDataFile(maxAmounts, startPage = 1) {
    // Counter Variable zum Erfassen, wie viele Einträge der verschiedenen Typen bereits gemacht wurden
    const typeCounters = { song: 0, call: 0, "alarm call": 0};
    const overview = { song: [], call: [], "alarm call": []};

    // Startseite für die Iteration, welche bei Aufruf der Methode angegeben werden kann
    let page = startPage;

    // Solange die Anzahl der Einträge eines Typs kleiner ist als die maximale Anzahl, wird weiter iteriert
    while (Object.entries(typeCounters).some(([type, count]) => count < maxAmounts[type])) {
        // URL für die aktuelle Seite
        const pageUrl = `${targetUrl}&pg=${page}`;
        // Axios-Request, um die HTML-Daten der Seite zu bekommen
        const pageData = await fetchWithRetry(pageUrl, {
            headers: { 'Accept-Language': 'de' }
        });

        // Schleife, falls die Seite auch mehrmals hintereinander nicht geladen werden konnte, dass die Seite übersprungen wird
        if (!pageData) {
            console.warn(`Seite ${page} übersprungen wegen wiederholtem 503.`);
            page++;
            continue;
        }

        // Das Plugin Cheerio wird verwendet, um die HTML-Daten zu parsen und die Tabelle mit den Ergebnissen zu extrahieren
        const $ = cheerio.load(pageData.data);
        // Extraktion der relevanten Tabelle aus dem HTML Code
        const firstTable = $('table.results').first();

        // Wenn auf der Seite keine Ergebnistabelle gefunden wird, wird die Methode abgebrochen
        if (!firstTable || firstTable.length === 0) {
            console.warn(`Keine Ergebnistabelle gefunden (Seite ${page}).`);
            return overview;
        }

        // Extraktion der Zeilen aus der Tabelle
        const rows = firstTable.find('tr');
        const dataRows = rows.filter((i, row) => $(row).find('td').length > 0);

        // Wenn die Tabelle leer ist, wird die Methode abgebrochen. Dies passiert normalerweise, wenn die letzte Seite erreicht ist und die Methode noch nicht die maximale Anzahl an Einträgen erreicht hat.
        if (dataRows.length === 0) {
            console.warn(`Letzte Seite erreicht (Seite ${page}). Einige Typen haben möglicherweise nicht die gewünschte Anzahl an Einträgen.`);
            return overview;
        }

        // Iterieren über die Zeilen der Tabelle
        rows.each((index, row) => {
            const cells = $(row).find('td');
            if (cells.length > 0) {
                // Extraktion des Namen der Vogelart
                const bird = $(cells[1]).find('span.common-name').text().trim();
                if (bird !== birdName) {
                    return;
                }
                // Extraktion der Länge des Files
                const length = $(cells[2]).text().trim();

                // Überprüfung, ob die Länge des Files kleiner als 5 Minuten ist
                const [minutes] = length.split(':').map(Number);
                if (minutes > 5 || (minutes === 5)) {
                    return;
                }

                // Extraktion des Landes der Aufnahme
                const country = $(cells[6]).text().trim();
                // Extraktion des Typs: Song, Call, Alarm Call
                const Type = $(cells[9]).text().trim().toLowerCase();
                // Extraktion der Qualität des Files (A-E)
                const Quality = $(cells[11]).find('li.selected').text().trim();
                // Extraktion des Downloadlinks
                const downloadLink = $(cells[11]).find('a').attr('href');
                // Erstellung eines Titels der Datei auf Basis der zuvor extrahierten Daten
                const title = `${bird}_(${length.replace(':', '_')})_${country.replace(' ', '')}_${Type.replace(' ', '')}_${Quality}`;
                console.log(`Processing bird: ${bird + ' - ' + page + ' - ' + Type + ' - ' + title}`);
                console.log('TypeCounters:', typeCounters);

                // Überprüfung, ob der Typ in der Liste der gewünschten Typen ist und ob die maximale Anzahl an Files des jeweiligen Typs noch nicht erreicht ist
                if (["song", "call", "alarm call"].includes(Type) && typeCounters[Type] < maxAmounts[Type]) {
                    // Push der Daten in das entsprechende Array im Overview-Objekt
                    overview[Type].push({
                        title: title,
                        bird: bird,
                        length: length,
                        country: country,
                        Type: Type.replace(/ /g, ''),
                        Quality: Quality,
                        downloadLink: downloadLink,
                        page: page
                    });
                    // Erhöhung des Counters für den jeweiligen Typ
                    typeCounters[Type]++;
                }
            }
        });
        // Erhöhung der Seitenzahl für die nächste Iteration
        page++;
    }

    return overview;
}

async function downloadWithRetry(url, fileName, retries = 3, delay = 2000) {
    for (let i = 0; i < retries; i++) {
        const fileStream = fs.createWriteStream(fileName);
        try {
            // Herunterladen der MP3-Datei
            const response = await axios.get(url, { responseType: 'stream' });

            // Überprüfen, ob die Antwort erfolgreich war
            response.data.pipe(fileStream);

            // Warten, bis der Download abgeschlossen ist und eine Response zurückgegeben wird
            await new Promise((resolve, reject) => {
                fileStream.once('finish', () => resolve());
                fileStream.once('error', () => reject());
            });
            console.log(`Downloaded ${fileName}`);
            return;

        } catch (error) {
            fileStream.close();
            // Löschen der Datei, falls der Download fehlschlägt
            fs.unlinkSync(fileName);
            // Versuch Datei erneut herunterzuladen, falls ein 503 Fehler auftritt
            if (error.response && error.response.status === 503 && i < retries - 1) {
                console.warn(`503 beim Download, versuche erneut in 5 Sekunden...` + error);
                // Timeout wird gesetzt und Promise wird abgewartet
                await new Promise(res => setTimeout(res, delay));
            } else {
                throw error;
            }
        }
    }
}

// Funktion zum Schreiben der Daten in mehrere JSON-Dateien und Herunterladen der MP3-Dateien
async function writeJsonAndDownloadFiles(overview) {
    // Erstellen der Hauptordnerstruktur
    for (const type in overview) {
        const typeFolderName = type.replace(/ /g, '');
        const typeFolder = path.join(downloadDir, typeFolderName);

        // Überprüfen, ob der Ordner für den jeweiligen Typ bereits existiert, und erstellen, falls nicht
        if (!fs.existsSync(typeFolder)) {
            fs.mkdirSync(typeFolder);
        }

        // Schreiben der JSON-Datei für den jeweiligen Typ
        const jsonFilePath = path.join(typeFolder, `${typeFolderName}.json`);
        fs.writeFileSync(jsonFilePath, JSON.stringify(overview[type], null, 2));

        for (const item of overview[type]) {
            const fileName = path.join(typeFolder, `${item.title}.mp3`);
            try {
                // Herunterladen der MP3-Datei mit Retry-Mechanismus über die Funktion downloadWithRetry
                await downloadWithRetry(item.downloadLink, fileName);
            } catch (error) {
                console.error(`Error downloading ${fileName}:`, error);
            }
        }
    }
}

// Hauptfunktion, die die Daten abruft und die Dateien herunterlädt
async function main() {
    // Definieren der maximalen Anzahl an Einträgen pro Typ
    const maxAmounts = { song: 40, call: 40, "alarm call": 40};
    const overview = await getDataFile(maxAmounts, startPage = 1);
    await writeJsonAndDownloadFiles(overview);
}

main();