// Mock Test Engine for TalathiIQ
let mockQuestions = [];
let currentQuestionIndex = 0;
let userAnswers = []; // Holds selected index (0-3) or null
let flaggedStatus = []; // Holds true or false
let timerInterval = null;
let timeRemaining = 1200; // minutes in seconds
let totalTime = 1200;

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === '/mock-test') {
        setupConfigPanel();
        
        // Auto-start paper test if specified in URL
        const urlParams = new URLSearchParams(window.location.search);
        const paper = urlParams.get('paper');
        if (paper) {
            startPaperMockTest(paper);
        }
    }
});

async function startPaperMockTest(paperId) {
    const configContainer = document.getElementById('configContainer');
    if (configContainer) configContainer.style.display = 'none';
    
    const testContainer = document.getElementById('testContainer');
    if (testContainer) testContainer.style.display = 'grid';
    
    try {
        const response = await fetch(`/api/questions?paper=${paperId}`);
        mockQuestions = await response.json();
        
        if (mockQuestions.length === 0) {
            alert("No questions found for this paper.");
            window.location.href = '/pyq-papers';
            return;
        }
        
        totalTime = mockQuestions.length * 36;
        timeRemaining = totalTime;
        userAnswers = Array(mockQuestions.length).fill(null);
        flaggedStatus = Array(mockQuestions.length).fill(false);
        currentQuestionIndex = 0;
        
        renderNavGrid();
        renderMockQuestion();
        startMockTimer();
        
        const prevBtn = document.getElementById('prevMockBtn');
        const nextBtn = document.getElementById('nextMockBtn');
        const flagBtn = document.getElementById('markReviewBtn');
        const submitBtn = document.getElementById('submitTestBtn');
        
        const newPrev = prevBtn.cloneNode(true);
        const newNext = nextBtn.cloneNode(true);
        const newFlag = flagBtn.cloneNode(true);
        const newSubmit = submitBtn.cloneNode(true);
        
        prevBtn.replaceWith(newPrev);
        nextBtn.replaceWith(newNext);
        flagBtn.replaceWith(newFlag);
        submitBtn.replaceWith(newSubmit);
        
        newPrev.addEventListener('click', () => navigateTo(currentQuestionIndex - 1));
        newNext.addEventListener('click', () => navigateTo(currentQuestionIndex + 1));
        newFlag.addEventListener('click', toggleMarkForReview);
        newSubmit.addEventListener('click', confirmSubmitTest);
    } catch (error) {
        console.error("Error starting paper mock test:", error);
        alert("Failed to start exam. Redirecting back to papers.");
        window.location.href = '/pyq-papers';
    }
}


function setupConfigPanel() {
    // Handle radio selector visual active state toggle
    const radioGroups = ['dbSource', 'difficulty', 'qLimit'];
    radioGroups.forEach(groupName => {
        const radios = document.querySelectorAll(`input[name="${groupName}"]`);
        radios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                // Remove active class from all sibling labels
                radios.forEach(r => {
                    r.parentElement.classList.remove('active');
                });
                // Add active to selected label
                if (e.target.checked) {
                    e.target.parentElement.classList.add('active');
                }
            });
        });
    });

    // Start test button
    const startBtn = document.getElementById('startTestBtn');
    if (startBtn) {
        startBtn.addEventListener('click', startConfiguredMockTest);
    }
}

async function startConfiguredMockTest() {
    const source = document.querySelector('input[name="dbSource"]:checked').value;
    const difficulty = document.querySelector('input[name="difficulty"]:checked').value;
    const limit = parseInt(document.querySelector('input[name="qLimit"]:checked').value, 10);
    const subject = document.querySelector('select[name="testSubject"]').value;

    const startBtn = document.getElementById('startTestBtn');
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Initializing Test...';

    try {
        const urlParams = new URLSearchParams(window.location.search);
        const stage = urlParams.get('stage') || localStorage.getItem('talathi_stage') || '';
        let url = `/api/questions?source=${source}&difficulty=${difficulty}&limit=${limit}&subject=${subject}`;
        if (stage) {
            url += `&stage=${stage}`;
        }
        const response = await fetch(url);
        mockQuestions = await response.json();

        if (mockQuestions.length === 0) {
            alert(`No questions found in the ${source} Database for ${subject} subject with ${difficulty} difficulty. Please select a different configuration.`);
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play"></i> Start Practice Session';
            return;
        }

        // Initialize state variables (36 seconds per question, making 100 questions = 60 minutes)
        totalTime = mockQuestions.length * 36;
        timeRemaining = totalTime;
        userAnswers = Array(mockQuestions.length).fill(null);
        flaggedStatus = Array(mockQuestions.length).fill(false);
        currentQuestionIndex = 0;

        // Hide config, show test container
        document.getElementById('configContainer').style.display = 'none';
        document.getElementById('testContainer').style.display = 'grid';

        // Render controls and initial questions
        renderNavGrid();
        renderMockQuestion();
        startMockTimer();

        // Bind Action Buttons (ensure bound only once)
        const prevBtn = document.getElementById('prevMockBtn');
        const nextBtn = document.getElementById('nextMockBtn');
        const flagBtn = document.getElementById('markReviewBtn');
        const submitBtn = document.getElementById('submitTestBtn');

        // Remove old listeners by cloning
        const newPrev = prevBtn.cloneNode(true);
        const newNext = nextBtn.cloneNode(true);
        const newFlag = flagBtn.cloneNode(true);
        const newSubmit = submitBtn.cloneNode(true);

        prevBtn.replaceWith(newPrev);
        nextBtn.replaceWith(newNext);
        flagBtn.replaceWith(newFlag);
        submitBtn.replaceWith(newSubmit);

        newPrev.addEventListener('click', () => navigateTo(currentQuestionIndex - 1));
        newNext.addEventListener('click', () => navigateTo(currentQuestionIndex + 1));
        newFlag.addEventListener('click', toggleMarkForReview);
        newSubmit.addEventListener('click', confirmSubmitTest);

    } catch (error) {
        console.error("Error starting mock test:", error);
        alert("Failed to start mock test. Please check server logs.");
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fas fa-play"></i> Start Practice Session';
    }
}

function renderNavGrid() {
    const grid = document.getElementById('questionsNavGrid');
    if (!grid) return;

    grid.innerHTML = '';
    mockQuestions.forEach((_, idx) => {
        const btn = document.createElement('button');
        btn.className = 'nav-grid-btn';
        btn.id = `nav-grid-${idx}`;
        btn.textContent = idx + 1;
        btn.addEventListener('click', () => navigateTo(idx));
        grid.appendChild(btn);
    });
    updateNavGridStyles();
}

function updateNavGridStyles() {
    mockQuestions.forEach((_, idx) => {
        const btn = document.getElementById(`nav-grid-${idx}`);
        if (!btn) return;

        btn.className = 'nav-grid-btn'; // Reset
        
        if (idx === currentQuestionIndex) {
            btn.classList.add('current');
        }
        
        if (flaggedStatus[idx]) {
            btn.classList.add('flagged');
        } else if (userAnswers[idx] !== null) {
            btn.classList.add('answered');
        }
    });
}

function renderMockQuestion() {
    if (mockQuestions.length === 0) return;

    const q = mockQuestions[currentQuestionIndex];

    // Meta elements
    const mockQuestionNum = document.getElementById('mockQuestionNum');
    const mockSubjectTag = document.getElementById('mockSubjectTag');
    
    if (mockQuestionNum) mockQuestionNum.textContent = `Question ${currentQuestionIndex + 1} of ${mockQuestions.length}`;
    if (mockSubjectTag) mockSubjectTag.textContent = (q.stage ? `[${q.stage}] ` : '') + q.subject + " | " + q.topic;

    // Text
    document.getElementById('mockQuestionText').textContent = q.question;

    // Options
    const container = document.getElementById('mockOptionsContainer');
    container.innerHTML = '';

    q.options.forEach((option, idx) => {
        const letter = String.fromCharCode(65 + idx);
        const button = document.createElement('button');
        button.className = 'option-btn';
        if (userAnswers[currentQuestionIndex] === idx) {
            button.classList.add('selected');
        }
        button.innerHTML = `
            <span class="option-marker">${letter}</span>
            <span class="option-label-text">${option}</span>
        `;
        button.addEventListener('click', () => selectMockOption(idx));
        container.appendChild(button);
    });

    // Control States
    document.getElementById('prevMockBtn').disabled = currentQuestionIndex === 0;
    document.getElementById('nextMockBtn').disabled = currentQuestionIndex === mockQuestions.length - 1;
    
    // Mark for Review toggle text
    const markReviewBtn = document.getElementById('markReviewBtn');
    if (flaggedStatus[currentQuestionIndex]) {
        markReviewBtn.innerHTML = '<i class="fas fa-flag"></i> Unmark';
    } else {
        markReviewBtn.innerHTML = '<i class="far fa-flag"></i> Mark for Review';
    }

    updateNavGridStyles();
}

function selectMockOption(index) {
    userAnswers[currentQuestionIndex] = index;
    
    // Auto remove flag on answer selection if preferred, or keep. Let's keep standard behavior.
    const optionBtns = document.querySelectorAll('#mockOptionsContainer .option-btn');
    optionBtns.forEach((btn, idx) => {
        if (idx === index) {
            btn.classList.add('selected');
        } else {
            btn.classList.remove('selected');
        }
    });

    updateNavGridStyles();
}

function toggleMarkForReview() {
    flaggedStatus[currentQuestionIndex] = !flaggedStatus[currentQuestionIndex];
    renderMockQuestion();
}

function navigateTo(index) {
    if (index >= 0 && index < mockQuestions.length) {
        currentQuestionIndex = index;
        renderMockQuestion();
    }
}

function startMockTimer() {
    const display = document.getElementById('mockTimer');
    timeRemaining = totalTime;

    timerInterval = setInterval(() => {
        timeRemaining--;
        if (display) {
            display.innerHTML = `<i class="far fa-clock"></i> ${formatTime(timeRemaining)}`;
        }

        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            alert("Time is up! Submitting your test automatically.");
            submitMockTest();
        }
    }, 1000);
}

function confirmSubmitTest() {
    const unattempted = userAnswers.filter(ans => ans === null).length;
    let confirmMsg = "Are you sure you want to submit the Mock Test?";
    if (unattempted > 0) {
        confirmMsg = `You have ${unattempted} unattempted questions. Are you sure you want to submit the Mock Test?`;
    }
    if (confirm(confirmMsg)) {
        submitMockTest();
    }
}

function submitMockTest() {
    clearInterval(timerInterval);

    let correct = 0;
    let incorrect = 0;
    let unattempted = 0;

    userAnswers.forEach((ans, idx) => {
        if (ans === null) {
            unattempted++;
        } else if (ans === mockQuestions[idx].answer) {
            correct++;
        } else {
            incorrect++;
            
            // Log wrong answer for revision
            const q = mockQuestions[idx];
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
    });

    const totalQuestions = mockQuestions.length;
    const score = correct * 2; // e.g. 2 marks per question
    const accuracy = (correct + incorrect) > 0 ? Math.round((correct / (correct + incorrect)) * 100) : 0;
    const timeTaken = totalTime - timeRemaining;

    // Save result details to local storage
    const mockResult = {
        score: score,
        maxScore: totalQuestions * 2,
        correct: correct,
        incorrect: incorrect,
        unattempted: unattempted,
        accuracy: accuracy,
        timeTaken: timeTaken,
        totalQuestions: totalQuestions
    };

    localStorage.setItem('talathi_last_mock_result', JSON.stringify(mockResult));

    // Update global statistics
    let stats = JSON.parse(localStorage.getItem('talathi_stats')) || {
        questionsSolved: 0,
        accuracy: 0,
        mockTestsTaken: 0,
        streak: 1
    };

    stats.questionsSolved += (correct + incorrect);
    stats.mockTestsTaken += 1;
    // Recalculate global average accuracy
    stats.accuracy = Math.round(((stats.accuracy * (stats.mockTestsTaken - 1)) + accuracy) / stats.mockTestsTaken);
    localStorage.setItem('talathi_stats', JSON.stringify(stats));

    // Redirect to results page
    window.location.href = '/result';
}
