// MCQ Practice engine for TalathiIQ
let questions = [];
let currentIndex = 0;
let answeredQuestions = {}; // Format: { questionId: { selectedIndex: X, isCorrect: true/false } }
let correctCount = 0;
let wrongCount = 0;
let currentSubject = '';

document.addEventListener('DOMContentLoaded', () => {
    fetchQuestions();

    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');

    if (prevBtn) prevBtn.addEventListener('click', showPreviousQuestion);
    if (nextBtn) nextBtn.addEventListener('click', showNextQuestion);
    if (submitBtn) submitBtn.addEventListener('click', submitAnswer);

    // Subject Filter Selection
    const subjectSelect = document.getElementById('subjectSelect');
    if (subjectSelect) {
        subjectSelect.addEventListener('change', (e) => {
            currentSubject = e.target.value;
            currentIndex = 0;
            answeredQuestions = {};
            correctCount = 0;
            wrongCount = 0;
            updateScorecard();
            fetchQuestions();
        });
    }
});

async function fetchQuestions() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const stage = urlParams.get('stage') || localStorage.getItem('talathi_stage') || '';
        let url = '/api/questions';
        let params = [];
        if (stage) {
            params.push(`stage=${stage}`);
        }
        if (currentSubject) {
            params.push(`subject=${encodeURIComponent(currentSubject)}`);
        }
        if (params.length > 0) {
            url += `?${params.join('&')}`;
        }
        const response = await fetch(url);
        questions = await response.json();
        if (questions && questions.length > 0) {
            renderQuestion();
        } else {
            document.getElementById('questionText').textContent = "No questions found. Please check data source.";
            document.getElementById('progressText').textContent = "Question 0 of 0";
            document.getElementById('progressFill').style.width = "0%";
            document.getElementById('optionsContainer').innerHTML = '';
            document.getElementById('subjectTag').textContent = "N/A";
            document.getElementById('difficultyTag').textContent = "N/A";
            document.getElementById('prevBtn').disabled = true;
            document.getElementById('nextBtn').disabled = true;
            document.getElementById('submitBtn').disabled = true;
        }
    } catch (error) {
        console.error("Error fetching questions:", error);
        document.getElementById('questionText').textContent = "Failed to load questions from server.";
    }
}

function renderQuestion() {
    if (questions.length === 0) return;

    const q = questions[currentIndex];
    
    // Update progress elements
    const progressText = document.getElementById('progressText');
    const progressFill = document.getElementById('progressFill');
    if (progressText) progressText.textContent = `Question ${currentIndex + 1} of ${questions.length}`;
    if (progressFill) progressFill.style.width = `${((currentIndex + 1) / questions.length) * 100}%`;

    // Render Meta
    const subjectTag = document.getElementById('subjectTag');
    const difficultyTag = document.getElementById('difficultyTag');
    if (subjectTag) subjectTag.textContent = (q.stage ? `[${q.stage}] ` : '') + q.subject + " | " + q.topic;
    if (difficultyTag) {
        difficultyTag.textContent = q.difficulty;
        difficultyTag.className = `difficulty-badge ${q.difficulty.toLowerCase()}`;
    }

    // Render Question Text
    const questionText = document.getElementById('questionText');
    if (questionText) questionText.textContent = q.question;

    // Render Options
    const optionsContainer = document.getElementById('optionsContainer');
    if (optionsContainer) {
        optionsContainer.innerHTML = '';
        q.options.forEach((option, idx) => {
            const letter = String.fromCharCode(65 + idx); // A, B, C, D
            const button = document.createElement('button');
            button.className = 'option-btn';
            button.innerHTML = `
                <span class="option-marker">${letter}</span>
                <span class="option-label-text">${option}</span>
            `;
            button.addEventListener('click', () => selectOption(idx));
            optionsContainer.appendChild(button);
        });
    }

    // Hide Explanation Panel
    const explanationPanel = document.getElementById('explanationPanel');
    if (explanationPanel) {
        explanationPanel.style.display = 'none';
        const explanationText = document.getElementById('explanationText');
        if (explanationText) explanationText.textContent = '';
    }

    // Restore State if already answered
    const prevAnswer = answeredQuestions[q.id];
    const submitBtn = document.getElementById('submitBtn');
    
    if (prevAnswer !== undefined) {
        const optionBtns = document.querySelectorAll('.option-btn');
        const selectedIdx = prevAnswer.selectedIndex;
        const correctIdx = q.answer;

        // Apply correct/wrong styles
        optionBtns.forEach((btn, idx) => {
            btn.disabled = true;
            if (idx === correctIdx) {
                btn.classList.add('correct');
            } else if (idx === selectedIdx && selectedIdx !== correctIdx) {
                btn.classList.add('wrong');
            }
        });

        // Show Explanation
        if (explanationPanel) {
            explanationPanel.style.display = 'block';
            document.getElementById('explanationText').textContent = q.explanation;
        }

        if (submitBtn) submitBtn.style.display = 'none';
    } else {
        if (submitBtn) {
            submitBtn.style.display = 'block';
            submitBtn.disabled = true; // Disabled until an option is clicked
        }
    }

    // Enable/disable navigation buttons
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    if (prevBtn) prevBtn.disabled = currentIndex === 0;
    if (nextBtn) nextBtn.disabled = currentIndex === questions.length - 1;
}

function selectOption(index) {
    const q = questions[currentIndex];
    // Don't allow selections if already answered
    if (answeredQuestions[q.id] !== undefined) return;

    const optionBtns = document.querySelectorAll('.option-btn');
    optionBtns.forEach((btn, idx) => {
        if (idx === index) {
            btn.classList.add('selected');
        } else {
            btn.classList.remove('selected');
        }
    });

    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) submitBtn.disabled = false;
}

function submitAnswer() {
    const q = questions[currentIndex];
    if (answeredQuestions[q.id] !== undefined) return;

    const selectedBtn = document.querySelector('.option-btn.selected');
    if (!selectedBtn) return;

    const optionBtns = Array.from(document.querySelectorAll('.option-btn'));
    const selectedIdx = optionBtns.indexOf(selectedBtn);
    const correctIdx = q.answer;
    const isCorrect = (selectedIdx === correctIdx);

    // Save state
    answeredQuestions[q.id] = {
        selectedIndex: selectedIdx,
        isCorrect: isCorrect
    };

    // Update Stats
    if (isCorrect) {
        correctCount++;
    } else {
        wrongCount++;
        // Track wrong questions for revision in localStorage
        let wrongList = JSON.parse(localStorage.getItem('talathi_wrong_questions')) || [];
        if (!wrongList.some(item => item.id === q.id)) {
            wrongList.push({
                id: q.id,
                question: q.question,
                subject: q.subject,
                topic: q.topic
            });
            localStorage.setItem('talathi_wrong_questions', JSON.stringify(wrongList));
        }
    }

    // Save global stats to localStorage
    let globalStats = JSON.parse(localStorage.getItem('talathi_stats')) || {};
    globalStats.questionsSolved = (globalStats.questionsSolved || 0) + 1;
    globalStats.accuracy = Math.round((correctCount / (correctCount + wrongCount)) * 100);
    localStorage.setItem('talathi_stats', JSON.stringify(globalStats));

    // Update Daily target progress
    if (typeof incrementDailyStat === 'function') {
        incrementDailyStat('questionsSolved', 1);
    }

    updateScorecard();

    // Render Answer Styles
    optionBtns.forEach((btn, idx) => {
        btn.disabled = true;
        btn.classList.remove('selected');
        if (idx === correctIdx) {
            btn.classList.add('correct');
        } else if (idx === selectedIdx && !isCorrect) {
            btn.classList.add('wrong');
        }
    });

    // Show Explanation
    const explanationPanel = document.getElementById('explanationPanel');
    if (explanationPanel) {
        explanationPanel.style.display = 'block';
        document.getElementById('explanationText').textContent = q.explanation;
    }

    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) submitBtn.style.display = 'none';
}

function updateScorecard() {
    const solvedCountEl = document.getElementById('solvedCount');
    const correctCountEl = document.getElementById('correctCount');
    const wrongCountEl = document.getElementById('wrongCount');
    const accuracyEl = document.getElementById('accuracyVal');

    const totalAnswered = correctCount + wrongCount;
    const accuracy = totalAnswered > 0 ? Math.round((correctCount / totalAnswered) * 100) : 0;

    if (solvedCountEl) solvedCountEl.textContent = totalAnswered;
    if (correctCountEl) correctCountEl.textContent = correctCount;
    if (wrongCountEl) wrongCountEl.textContent = wrongCount;
    if (accuracyEl) accuracyEl.textContent = accuracy + '%';
}

function showPreviousQuestion() {
    if (currentIndex > 0) {
        currentIndex--;
        renderQuestion();
    }
}

function showNextQuestion() {
    if (currentIndex < questions.length - 1) {
        currentIndex++;
        renderQuestion();
    }
}
