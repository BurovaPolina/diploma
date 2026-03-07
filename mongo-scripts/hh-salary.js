const { MongoClient } = require("mongodb");

const uri = "mongodb://localhost:27017"; // Подключение к локальному серверу MongoDB
const dbName = "hh"; // Замените на имя вашей БД
// const collectionName = "22-01-2025"; // Замените на имя вашей коллекции
const collectionName = "24-02-2025"; // Замените на имя вашей коллекции

async function calculateAverageSalary() {
  const client = new MongoClient(uri);

  try {
    await client.connect();
    console.log("Подключено к MongoDB");

    const db = client.db(dbName);
    const collection = db.collection(collectionName);

    const result = await collection.aggregate([
      {
        $match: { "salary": { $exists: true } }
      },
      {
        $project: {
          avgSalary: {
            $cond: {
              if: { $and: [{ $gt: ["$salary.from", null] }, { $gt: ["$salary.to", null] }] },
              then: { $avg: ["$salary.from", "$salary.to"] },
              else: { $ifNull: ["$salary.from", "$salary.to"] }
            }
          }
        }
      },
      {
        $group: {
          _id: null,
          averageSalary: { $avg: "$avgSalary" }
        }
      }
    ]).toArray();

    if (result.length > 0) {
      console.log("Средняя зарплата:", result[0].averageSalary);
    } else {
      console.log("Нет данных о зарплатах.");
    }

  } catch (error) {
    console.error("Ошибка:", error);
  } finally {
    await client.close();
    console.log("Соединение с MongoDB закрыто");
  }
}

calculateAverageSalary();