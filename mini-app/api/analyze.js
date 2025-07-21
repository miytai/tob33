import { AsyncOpenAI } from 'openai';

const client = new AsyncOpenAI(api_key: process.env.OPENAI_API_KEY);

export default async function handler(req, res) {
    if (req.method === 'POST') {
        // Анализ всего текста
        try {
            const { text } = req.body;
            const analysis = await analyzeFullText(text);
            res.status(200).json({ analysis });
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    } else if (req.method === 'GET') {
        // Анализ одного слова
        try {
            const { word } = req.query;
            const result = await analyzeSingleWord(word);
            res.status(200).json(result);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    } else {
        res.setHeader('Allow', ['GET', 'POST']);
        res.status(405).end(`Method ${req.method} Not Allowed`);
    }
}

async function analyzeFullText(text) {
    // Используем GPT для анализа текста и поиска ошибок
    const response = await client.chat.completions.create({
        model: "gpt-4",
        messages: [{
            role: "system",
            content: `Ты эксперт по ивриту. Проанализируй текст и верни JSON массив, где каждый элемент содержит:
- word: слово
- isCorrect: boolean (правильно ли написано)
- correction: предложенное исправление (если есть ошибка)`
        }, {
            role: "user",
            content: text
        }],
        temperature: 0.3,
        response_format: { type: "json_object" }
    });
    
    return JSON.parse(response.choices[0].message.content).analysis;
}

async function analyzeSingleWord(word) {
    // Анализ одного слова (как в вашем исходном коде)
    const response = await client.chat.completions.create({
        model: "gpt-4",
        messages: [{
            role: "system",
            content: "Ты помощник для изучения иврита. Дай транскрипцию, перевод, объяснение и синонимы для слова."
        }, {
            role: "user",
            content: `Слово: ${word}\n\nДай:
1. Транскрипцию на русском
2. Перевод
3. Краткое объяснение
4. Синонимы (если есть)`
        }],
        temperature: 0.3
    });
    
    const result = response.choices[0].message.content;
    return {
        transcription: extractPart(result, "Транскрипция:"),
        translation: extractPart(result, "Перевод:"),
        explanation: extractPart(result, "Объяснение:"),
        synonyms: extractPart(result, "Синонимы:")
    };
}

function extractPart(text, prefix) {
    if (!text.includes(prefix)) return null;
    return text.split(prefix)[1].split("\n")[0].trim();
}