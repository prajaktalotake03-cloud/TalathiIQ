// Dashboard stats rendering and Stage Switcher
document.addEventListener('DOMContentLoaded', () => {
    // Check if we have localStorage data, otherwise seed defaults
    let stats = JSON.parse(localStorage.getItem('talathi_stats')) || {
        questionsSolved: 142,
        accuracy: 78,
        mockTestsTaken: 3,
        streak: 5,
        wrongCount: 12,
        savedCount: 8
    };

    // Save in localStorage if it wasn't there
    if (!localStorage.getItem('talathi_stats')) {
        localStorage.setItem('talathi_stats', JSON.stringify(stats));
    }

    // Populate dashboard statistics if the elements exist
    const elements = {
        'solvedCount': stats.questionsSolved,
        'accuracyVal': stats.accuracy + '%',
        'mockCount': stats.mockTestsTaken,
        'streakDays': stats.streak + ' Days',
        'solvedCountHero': stats.questionsSolved + '+',
        'wrongCount': stats.wrongCount,
        'savedCount': stats.savedCount
    };

    for (const [id, value] of Object.entries(elements)) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
        }
    }

    // Stage Selector Logic
    const currentStage = localStorage.getItem('talathi_stage') || 'Prelims';
    updateStageUI(currentStage);

    const btnPrelims = document.getElementById('btnPrelims');
    const btnMains = document.getElementById('btnMains');

    if (btnPrelims) {
        btnPrelims.addEventListener('click', () => {
            setExamStage('Prelims');
        });
    }
    if (btnMains) {
        btnMains.addEventListener('click', () => {
            setExamStage('Mains');
        });
    }
});

function setExamStage(stage) {
    localStorage.setItem('talathi_stage', stage);
    updateStageUI(stage);
}

function updateStageUI(stage) {
    const btnPrelims = document.getElementById('btnPrelims');
    const btnMains = document.getElementById('btnMains');
    
    if (stage === 'Prelims') {
        if (btnPrelims) btnPrelims.classList.add('active');
        if (btnMains) btnMains.classList.remove('active');
    } else {
        if (btnPrelims) btnPrelims.classList.remove('active');
        if (btnMains) btnMains.classList.add('active');
    }

    // Update hero links and card action links to append ?stage=Prelims or ?stage=Mains
    // Hero buttons
    const heroMCQ = document.querySelector('.hero-buttons a[href*="/mcq"]');
    const heroMock = document.querySelector('.hero-buttons a[href*="/mock-test"]');
    // Card actions
    const cardMCQ = document.querySelector('.card a[href*="/mcq"]');
    const cardMock = document.querySelector('.card a[href*="/mock-test"]');

    if (heroMCQ) heroMCQ.setAttribute('href', `/mcq?stage=${stage}`);
    if (heroMock) heroMock.setAttribute('href', `/mock-test?stage=${stage}`);
    if (cardMCQ) cardMCQ.setAttribute('href', `/mcq?stage=${stage}`);
    if (cardMock) cardMock.setAttribute('href', `/mock-test?stage=${stage}`);
}
