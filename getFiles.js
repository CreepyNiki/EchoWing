const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');

const birdName = 'Blaumeise';
const targetUrl = 'https://xeno-canto.org/explore?query=' + encodeURIComponent(birdName);
const downloadDir = path.join(__dirname, 'Files', birdName);

// Cleanup der alten Ordnerstruktur
if (fs.existsSync(downloadDir)) {
    fs.rmSync(downloadDir, { recursive: true, force: true });
}

// Erstellen des neuen Folders
fs.mkdirSync(downloadDir);

// Funktion zur Datenextraktion von der Seite xeno-canto
async function getDataFile(maxAmount) {
    // Counter Variable zum Erfassen, wie viele Einträge der verschiedenen Typen bereits gemacht wurden
    const typeCounters = { song: 0, call: 0, "alarm call": 0, "begging call": 0 };
    // Arrays, wo die Daten reingepusht werden
    const overview = { song: [], call: [], "alarm call": [], "begging call": [] };
    // Variable für die Seitenanzahl, um die verschiedenen Pages der Suchanfrage durchzugehen
    let page = 1;

    // Loop, der so lange läuft, bis die maximale Anzahl an Einträgen für jeden Typ erreicht ist
    while (Object.values(typeCounters).some(count => count < maxAmount)) {
        // URL für die aktuelle Seite
        const pageUrl = `${targetUrl}&pg=${page}`;
        // Axios-Request, um die HTML-Daten der Seite zu bekommen
        const pageData = await axios.get(pageUrl, {
            headers: {
                'Accept-Language': 'de',
            }
        }).then(response => response.data)

        const $ = cheerio.load(pageData);
        // Extraktion der relevanten Tabelle aus dem HTML Code
        const firstTable = $('table.results').first();
        const rows = firstTable.find('tr');

        // Abbruchbedingung: Wenn die letzte Seite erreicht ist stoppt der Loop
        if (rows.length === 0) {
            console.warn(`Letzte Seite erreicht (Seite ${page}). Einige Typen haben möglicherweise nicht die gewünschte Anzahl an Einträgen.`);
            break;
        }

        // Iterieren über die Zeilen der Tabelle
        rows.each((index, row) => {
            const cells = $(row).find('td');
            if (cells.length > 0) {
                // Extraktion des Namen der Vogelart
                const bird = $(cells[1]).find('span.common-name').text().trim();
                // Extraktion der Länge des Files
                const length = $(cells[2]).text().trim();

                // Überprüfung, ob die Länge des Files kleiner als 1:30 ist
                const [minutes, seconds] = length.split(':').map(Number);
                if (minutes > 1 || (minutes === 1 && seconds > 30)) {
                    return;
                }

                // Extraktion des Landes der Aufnahme
                const country = $(cells[6]).text().trim();
                // Extraktion des Typs: Song, Call, Alarm Call, Begging Call
                const Type = $(cells[9]).text().trim().toLowerCase();
                // Extraktion der Qualität des Files (A-E)
                const Quality = $(cells[11]).find('li.selected').text().trim();
                // Extraktion des Downloadlinks
                const downloadLink = $(cells[11]).find('a').attr('href');
                // Erstellung eines Titels der Datei aus den zuvor extrahierten Daten
                const title = `${bird}_(${length.replace(':', '_')})_${country}_${Type}_${Quality}`;

                // Überprüfung, ob der Typ in der Liste der gewünschten Typen ist und ob die maximale Anzahl an Files des jeweiligen Typs noch nicht erreicht ist
                if (["song", "call", "alarm call", "begging call"].includes(Type) && typeCounters[Type] < maxAmount) {
                    overview[Type].push({
                        title: title,
                        bird: bird,
                        length: length,
                        country: country,
                        Type: Type,
                        Quality: Quality,
                        downloadLink: downloadLink,
                        page: page
                    });
                    typeCounters[Type]++;
                }
            }
        });

        page++;
    }

    return overview;
}

// Funktion zum Schreiben der Daten in mehrere JSON-Dateien und Herunterladen der MP3-Dateien
async function writeJsonAndDownloadFiles(overview) {
    // Erstellen der Hauptordnerstruktur
    for (const type in overview) {
        const typeFolder = path.join(downloadDir, type);

        // Überprüfen, ob der Ordner für den jeweiligen Typ bereits existiert, und erstellen, falls nicht
        if (!fs.existsSync(typeFolder)) {
            fs.mkdirSync(typeFolder);
        }

        // Schreiben der JSON-Datei für den jeweiligen Typ
        const jsonFilePath = path.join(typeFolder, `${type}.json`);
        fs.writeFileSync(jsonFilePath, JSON.stringify(overview[type], null, 2));

        for (const item of overview[type]) {
            const fileName = path.join(typeFolder, `${item.title}.mp3`);
            const fileStream = fs.createWriteStream(fileName);

            try {
                // Herunterladen der MP3-Datei
                const response = await axios.get(item.downloadLink, { responseType: 'stream' });

                // Überprüfen, ob die Antwort erfolgreich war
                response.data.pipe(fileStream);

                // Warten, bis der Download abgeschlossen ist und eine Response zurückgegeben wird
                await new Promise((resolve, reject) => {
                    fileStream.once('finish', resolve);
                    fileStream.once('error', reject);
                });

                // Printausgabe, dass der Download erfolgreich war
                console.log(`Downloaded ${fileName}`);
            } catch (error) {
                console.error(`Error downloading ${fileName}:`, error);
            }
        }
    }
}

// Hauptfunktion, die die Daten abruft und die Dateien herunterlädt
async function main() {
    const overview = await getDataFile(40);
    await writeJsonAndDownloadFiles(overview);
}

main();