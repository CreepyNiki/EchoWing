const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: require('path').join(__dirname, '..', '.env') });

const birdName = process.env.birdName;
const targetUrl = 'https://xeno-canto.org/explore?query=' + encodeURIComponent(birdName);
console.log(targetUrl);
const downloadDir = path.join(__dirname, '../SoundFiles', birdName);

// Cleanup der alten Ordnerstruktur
if (fs.existsSync(downloadDir)) {
    fs.rmSync(downloadDir, { recursive: true, force: true });
}

// Erstellen des neuen Folders
fs.mkdirSync(downloadDir);

async function fetchWithRetry(url, options = {}, retries = 3, delay = 5000) {
    for (let i = 0; i < retries; i++) {
        try {
            return await axios.get(url, options);
        } catch (error) {
            if (error.response && error.response.status === 503 && i < retries - 1) {
                console.warn(`503 erhalten, versuche erneut in ${delay}ms...`);
                await new Promise(res => setTimeout(res, delay));
            } else {
                throw error;
            }
        }
    }
}

// Funktion zur Datenextraktion von der Seite xeno-canto
async function getDataFile(maxAmounts, startPage = 1) {
    const typeCounters = { song: 0, call: 0, "alarm call": 0, "flight call": 0 };
    const overview = { song: [], call: [], "alarm call": [], "flight call": [] };
    let page = startPage;

    while (Object.entries(typeCounters).some(([type, count]) => count < maxAmounts[type])) {
        const pageUrl = `${targetUrl}&pg=${page}`;
        const pageData = await fetchWithRetry(pageUrl, {
            headers: { 'Accept-Language': 'de' }
        });
        if (!pageData) {
            console.warn(`Seite ${page} übersprungen wegen wiederholtem 503.`);
            page++;
            continue;
        }

        const $ = cheerio.load(pageData.data);
        const firstTable = $('table.results').first();
        if (!firstTable || firstTable.length === 0) {
            console.warn(`Keine Ergebnistabelle gefunden (Seite ${page}).`);
            return overview;
        }
        const rows = firstTable.find('tr');
        const dataRows = rows.filter((i, row) => $(row).find('td').length > 0);

        if (dataRows.length === 0) {
            console.warn(`Letzte Seite erreicht (Seite ${page}). Einige Typen haben möglicherweise nicht die gewünschte Anzahl an Einträgen.`);
            return overview;
        }

        rows.each((index, row) => {
            const cells = $(row).find('td');
            if (cells.length > 0) {
                const bird = $(cells[1]).find('span.common-name').text().trim();
                if (bird !== birdName) {
                    return;
                }
                console.log(`Processing bird: ${bird + ' - ' + page}`);
                const length = $(cells[2]).text().trim();
                const [minutes] = length.split(':').map(Number);
                if (minutes > 5 || (minutes === 5)) {
                    return;
                }

                const country = $(cells[6]).text().trim();
                // Extraktion des Typs: Song, Call, Alarm Call, Flight Call
                const Type = $(cells[9]).text().trim().toLowerCase();
                const Quality = $(cells[11]).find('li.selected').text().trim();
                const downloadLink = $(cells[11]).find('a').attr('href');
                const title = `${bird}_(${length.replace(':', '_')})_${country.replace(' ', '')}_${Type.replace(' ', '')}_${Quality}`;
                console.log(`Processing bird: ${bird + ' - ' + page + ' - ' + Type + ' - ' + title}`);
                console.log('TypeCounters:', typeCounters);
                if (["song", "call", "alarm call", "flight call"].includes(Type) && typeCounters[Type] < maxAmounts[Type]) {
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
                    typeCounters[Type]++;
                }
            }
        });

        page++;
    }

    return overview;
}

async function downloadWithRetry(url, fileName, retries = 3, delay = 2000) {
    for (let i = 0; i < retries; i++) {
        const fileStream = fs.createWriteStream(fileName);
        try {
            const response = await axios.get(url, { responseType: 'stream' });
            response.data.pipe(fileStream);
            await new Promise((resolve, reject) => {
                fileStream.once('finish', resolve);
                fileStream.once('error', reject);
            });
            console.log(`Downloaded ${fileName}`);
            return;
        } catch (error) {
            fileStream.close();
            fs.unlinkSync(fileName);
            if (error.response && error.response.status === 503 && i < retries - 1) {
                console.warn(`503 beim Download, versuche erneut in ${delay}ms...` + error);
                await new Promise(res => setTimeout(res, delay));
            } else {
                throw error;
            }
        }
    }
}

async function writeJsonAndDownloadFiles(overview) {
    for (const type in overview) {
        const typeFolderName = type.replace(/ /g, '');
        const typeFolder = path.join(downloadDir, typeFolderName);

        if (!fs.existsSync(typeFolder)) {
            fs.mkdirSync(typeFolder);
        }

        const jsonFilePath = path.join(typeFolder, `${typeFolderName}.json`);
        fs.writeFileSync(jsonFilePath, JSON.stringify(overview[type], null, 2));

        for (const item of overview[type]) {
            const fileName = path.join(typeFolder, `${item.title}.mp3`);
            try {
                await downloadWithRetry(item.downloadLink, fileName);
            } catch (error) {
                console.error(`Error downloading ${fileName}:`, error);
            }
        }
    }
}

async function main() {
    const maxAmounts = { song: 40, call: 40, "alarm call": 40, "flight call": 80 };
    const overview = await getDataFile(maxAmounts, startPage = 1);
    await writeJsonAndDownloadFiles(overview);
}

main();