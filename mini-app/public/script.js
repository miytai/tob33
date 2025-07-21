document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const text = urlParams.get('text') || '';
    
    if (text) {
        analyzeText(text);
    }
});

async function analyzeText(text) {
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        
        const data = await response.json();
        displayTextWithAnalysis(data.analysis);
    } catch (error) {
        console.error('Error analyzing text:', error);
        displayPlainText(text);
    }
}

function displayTextWithAnalysis(analysis) {
    const textDisplay = document.getElementById('text-display');
    textDisplay.innerHTML = '';
    
    analysis.forEach(item => {
        const wordSpan = document.createElement('span');
        wordSpan.className = `word ${item.isCorrect ? 'correct' : 'incorrect'}`;
        wordSpan.textContent = item.word + ' ';
        wordSpan.dataset.word = item.word;
        
        if (!item.isCorrect) {
            const tooltip = document.createElement('span');
            tooltip.className = 'tooltip';
            tooltip.textContent = `Исправление: ${item.correction}`;
            wordSpan.appendChild(tooltip);
        }
        
        wordSpan.addEventListener('click', () => showWordDetails(item.word));
        textDisplay.appendChild(wordSpan);
    });
}

function displayPlainText(text) {
    const textDisplay = document.getElementById('text-display');
    textDisplay.textContent = text;
    
    // Добавляем обработчики кликов на слова
    const words = text.split(/\s+/);
    textDisplay.innerHTML = words.map(word => 
        `<span class="word" data-word="${word}">${word} </span>`
    ).join('');
    
    document.querySelectorAll('.word').forEach(el => {
        el.addEventListener('click', () => showWordDetails(el.dataset.word));
    });
}