const { MongoClient } = require("mongodb");
const fs = require('fs');

const uri = "mongodb://localhost:27017"; // Подключение к локальному серверу MongoDB
const dbName = "hh"; // Замените на имя вашей БД
// const collectionName = "22-01-2025"; // Замените на имя вашей коллекции
const collectionName = "24-02-2025"; // Замените на имя вашей коллекции

async function calculateSalaryRanges() {
    const client = new MongoClient(uri);

    try {
        await client.connect();
        console.log("Подключено к MongoDB");

        const db = client.db(dbName);
        const collection = db.collection(collectionName);

        // Найдем максимальную зарплату, чтобы определить диапазоны
        const maxSalaryDoc = await collection.aggregate([
            {
                $project: {
                    maxSalary: { $max: ["$salary.from", "$salary.to"] }
                }
            },
            {
                $group: {
                    _id: null,
                    maxSalary: { $max: "$maxSalary" }
                }
            }
        ]).toArray();

        const maxSalary = maxSalaryDoc.length > 0 ? maxSalaryDoc[0].maxSalary : 100000;
        const salaryRanges = [];
        for (let i = 20; i <= maxSalary / 1000; i += 10) {
            salaryRanges.push({ min: i * 1000, max: (i + 10) * 1000 });
        }

        const results = await Promise.all(
            salaryRanges.map(async (range) => {
                const vacancies = await collection
                    .find({
                        $or: [
                            { "salary.from": { $gte: range.min, $lt: range.max } },
                            { "salary.to": { $gte: range.min, $lt: range.max } }
                        ]
                    }, { projection: { _id: 1, id: 1, name: 1 } })
                    .toArray();

                return {
                    range: `${range.min} - ${range.max}`,
                    count: vacancies.length,
                    vacancies: vacancies.map(v => ({ id: v.id, name: v.name }))
                };
            })
        );
        const data = JSON.stringify(results, null, 2);
        console.log();

        fs.writeFile(`${collectionName}.json`, data, (err) => {
            // если произошла ошибка, выбрасываем исключение
            if (err) throw err;
            // выводим сообщение об успешной записи
            console.log('Данные сохранены в файл');
        });


    } catch (error) {
        console.error("Ошибка:", error);
    } finally {
        await client.close();
        console.log("Соединение с MongoDB закрыто");
    }
}

calculateSalaryRanges();