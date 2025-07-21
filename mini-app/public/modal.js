const modal = document.getElementById('modal');
const modalTitle = document.getElementById('word-title');
const modalContent = document.getElementById('word-info');
const closeBtn = document.querySelector('.close');

function showWordDetails(word) {
    modalTitle.textContent = word;
    modalContent.innerHTML = '<p>Загрузка информации...</p>';
    modal.style.display = 'block';
    
    fetchWordDetails(word);
}

async function fetchWordDetails(word) {
    try {
        const response = await fetch(`/api/analyze?word=${encodeURIComponent(word)}`);
        const data = await response.json();
        
        modalContent.innerHTML = `
            <div class="word-info-item">
                <span class="word-info-label">Транскрипция:</span>
                <span>${data.transcription || 'N/A'}</span>
            </div>
            <div class="word-info-item">
                <span class="word-info-label">Перевод:</span>
                <span>${data.translation || 'N/A'}</span>
            </div>
            <div class="word-info-item">
                <span class="word-info-label">Объяснение:</span>
                <span>${data.explanation || 'N/A'}</span>
            </div>
            ${data.synonyms ? `
            <div class="word-info-item">
                <span class="word-info-label">Синонимы:</span>
                <span>${data.synonyms}</span>
            </div>
            ` : ''}
        `;
    } catch (error) {
        console.error('Error fetching word details:', error);
        modalContent.innerHTML = '<p>Не удалось загрузить информацию о слове</p>';
    }
}

closeBtn.addEventListener('click', () => {
    modal.style.display = 'none';
});

window.addEventListener('click', (event) => {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});