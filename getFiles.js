const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');

const birdName = 'Blaumeise';
const targetUrl = 'https://xeno-canto.org/explore?query=' + encodeURIComponent(birdName);
const downloadDir = path.join(__dirname, 'Files', birdName);

if (fs.existsSync(downloadDir)) {
    fs.rmSync(downloadDir, { recursive: true, force: true });
}
fs.mkdirSync(downloadDir);

async function getDataFile(maxAmount) {
    const typeCounters = { song: 0, call: 0, "alarm call": 0, "begging call": 0 };
    const overview = { song: [], call: [], "alarm call": [], "begging call": [] };
    let page = 1;

    while (Object.values(typeCounters).some(count => count < maxAmount)) {
        const pageUrl = `${targetUrl}&pg=${page}`;
        const pageData = await fetchPage(pageUrl);

        if (!pageData) {
            console.error(`Failed to fetch data for page ${page}`);
            break;
        }

        const $ = cheerio.load(pageData);
        const firstTable = $('table.results').first();
        const rows = firstTable.find('tr');
        let newDataAdded = false;

        rows.each((index, row) => {
            const cells = $(row).find('td');
            if (cells.length > 0) {
                const bird = $(cells[1]).find('span.common-name').text().trim();
                const length = $(cells[2]).text().trim();

                const [minutes, seconds] = length.split(':').map(Number);
                if (minutes > 1 || (minutes === 1 && seconds > 30)) {
                    return;
                }

                const country = $(cells[6]).text().trim();
                const Type = $(cells[9]).text().trim().toLowerCase(); // Extract type and normalize case
                const Quality = $(cells[11]).find('li.selected').text().trim();
                const downloadLink = $(cells[11]).find('a').attr('href');
                const title = `${bird}_(${length.replace(':', '_')})_${country}_${Type}_${Quality}`;

                // Match exact types
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
                    newDataAdded = true;
                }
            }
        });

        if (!newDataAdded) {
            console.log(`No new data added on page ${page}. Stopping.`);
            break;
        }

        page++;
    }

    return overview;
}


async function writeJsonAndDownloadFiles(overview) {
    console.log(overview);
    for (const type in overview) {
        const typeFolder = path.join(downloadDir, type);

        // Create subfolder for the type
        if (!fs.existsSync(typeFolder)) {
            fs.mkdirSync(typeFolder);
        }

        // Write JSON file for the type
        const jsonFilePath = path.join(typeFolder, `${type}.json`);
        fs.writeFileSync(jsonFilePath, JSON.stringify(overview[type], null, 2));

        // Download MP3 files for the type
        for (const item of overview[type]) {
            const fileName = path.join(typeFolder, `${item.title}.mp3`);
            const fileStream = fs.createWriteStream(fileName);

            try {
                const response = await axios({
                    method: 'get',
                    url: item.downloadLink,
                    responseType: 'stream'
                });

                response.data.pipe(fileStream);
                await new Promise((resolve, reject) => {
                    fileStream.on('finish', resolve);
                    fileStream.on('error', reject);
                });

                console.log(`Downloaded ${fileName}`);
            } catch (error) {
                console.error(`Error downloading ${fileName}:`, error);
            }
        }
    }
}

async function fetchPage(url) {
    try {
        const response = await axios.get(url, {
            headers: {
                'Accept-Language': 'de',
            }
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching page:', error);
        return null;
    }
}

async function main() {
    const overview = await getDataFile(5);
    await writeJsonAndDownloadFiles(overview);
}

main();