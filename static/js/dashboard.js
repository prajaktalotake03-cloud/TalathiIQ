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

    // Load stage from localStorage or default to Prelims
    const activeStage = localStorage.getItem('talathi_stage') || 'Prelims';
    updateStageUI(activeStage);

    const btnPrelims = document.getElementById('btnPrelims');
    if (btnPrelims) {
        btnPrelims.addEventListener('click', () => {
            setExamStage('Prelims');
        });
    }

    const btnMains = document.getElementById('btnMains');
    if (btnMains) {
        btnMains.addEventListener('click', () => {
            setExamStage('Mains');
        });
    }

    // Initialize targets and update UI
    if (typeof updateTargetUI === 'function') {
        updateTargetUI();
    }

    // Initialize motivation widget
    initMotivationWidget();
    setInterval(initMotivationWidget, 5000);

    // Target Modal event listeners
    const targetBtn = document.getElementById('targetBtn');
    const targetModal = document.getElementById('targetModal');
    const targetClose = document.getElementById('targetClose');
    const targetSave = document.getElementById('targetSaveBtn');

    if (targetBtn && targetModal && targetClose) {
        targetBtn.addEventListener('click', () => {
            openTargetModal();
        });

        targetClose.addEventListener('click', () => {
            targetModal.classList.remove('active');
        });

        targetModal.addEventListener('click', (e) => {
            if (e.target === targetModal) {
                targetModal.classList.remove('active');
            }
        });
    }

    if (targetSave) {
        targetSave.addEventListener('click', () => {
            const mcqVal = parseInt(document.getElementById('inputMcqTarget').value) || 0;
            const mockVal = parseInt(document.getElementById('inputMockTarget').value) || 0;
            const timeVal = parseFloat(document.getElementById('inputTimeTarget').value) || 0;

            const targets = {
                questionsSolved: mcqVal,
                mockTestsTaken: mockVal,
                timeSpentSeconds: Math.round(timeVal * 3600)
            };

            saveDailyTargets(targets);
            updateTargetUI();
            targetModal.classList.remove('active');
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

    // Toggle subjects grid and syllabus overview
    const gridPrelims = document.getElementById('subjects-grid-prelims');
    const gridMains = document.getElementById('subjects-grid-mains');
    const overviewPrelims = document.getElementById('syllabus-overview-prelims');
    const overviewMains = document.getElementById('syllabus-overview-mains');

    if (stage === 'Prelims') {
        if (gridPrelims) gridPrelims.style.display = 'grid';
        if (gridMains) gridMains.style.display = 'none';
        if (overviewPrelims) overviewPrelims.style.display = 'block';
        if (overviewMains) overviewMains.style.display = 'none';
    } else {
        if (gridPrelims) gridPrelims.style.display = 'none';
        if (gridMains) gridMains.style.display = 'grid';
        if (overviewPrelims) overviewPrelims.style.display = 'none';
        if (overviewMains) overviewMains.style.display = 'block';
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

// Daily Target UI Manager functions
function openTargetModal() {
    const targetModal = document.getElementById('targetModal');
    if (targetModal) {
        targetModal.classList.add('active');
    }
    updateTargetUI();
}

function updateTargetUI() {
    if (typeof getDailyTargets !== 'function' || typeof getDailyProgress !== 'function') return;

    const targets = getDailyTargets();
    const progress = getDailyProgress();

    // Populate input controls inside modal
    const mcqInput = document.getElementById('inputMcqTarget');
    const mockInput = document.getElementById('inputMockTarget');
    const timeInput = document.getElementById('inputTimeTarget');

    if (mcqInput) mcqInput.value = targets.questionsSolved;
    if (mockInput) mockInput.value = targets.mockTestsTaken;
    if (timeInput) timeInput.value = (targets.timeSpentSeconds / 3600).toFixed(1);

    // Calculate percentage milestones
    const mcqPct = targets.questionsSolved > 0 ? Math.min(Math.round((progress.questionsSolved / targets.questionsSolved) * 100), 100) : 100;
    const mockPct = targets.mockTestsTaken > 0 ? Math.min(Math.round((progress.mockTestsTaken / targets.mockTestsTaken) * 100), 100) : 100;
    
    const timeSpentHours = progress.timeSpentSeconds / 3600;
    const targetHours = targets.timeSpentSeconds / 3600;
    const timePct = targets.timeSpentSeconds > 0 ? Math.min(Math.round((progress.timeSpentSeconds / targets.timeSpentSeconds) * 100), 100) : 100;

    // Update status labels
    setText('textMcqProgress', `${progress.questionsSolved} / ${targets.questionsSolved} MCQ`);
    setText('textMockProgress', `${progress.mockTestsTaken} / ${targets.mockTestsTaken} Tests`);
    setText('textTimeProgress', `${timeSpentHours.toFixed(1)}h / ${targetHours.toFixed(1)}h`);

    setText('textMcqPct', `${mcqPct}%`);
    setText('textMockPct', `${mockPct}%`);
    setText('textTimePct', `${timePct}%`);

    // Set widths of animated progress bar fills
    setBarWidth('barMcq', mcqPct);
    setBarWidth('barMock', mockPct);
    setBarWidth('barTime', timePct);

    // Update main Target button overall progress status
    const targetProgressText = document.getElementById('targetProgressText');
    if (targetProgressText) {
        const overallPct = Math.round((mcqPct + mockPct + timePct) / 3);
        targetProgressText.textContent = `(${overallPct}% Completed)`;
    }
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function setBarWidth(id, pct) {
    const el = document.getElementById(id);
    if (el) el.style.width = `${pct}%`;
}

function initMotivationWidget() {
    const quotes = [
        { text: "नवीन ध्येय ठरवण्यासाठी किंवा नवीन स्वप्न पाहण्यासाठी तुमचे वय कधीही जास्त नसते. 🎯", author: "अल्बर्ट आइनस्टाईन" },
        { text: "उद्याचे भविष्य हे आजच्या तयारीवर अवलंबून असते. अभ्यासात सातत्य ठेवा! 📚", author: "महात्मा गांधी" },
        { text: "अपयश म्हणजे संपुष्टात येणे नाही, तर नव्या जोमाने सुरुवात करण्याची सुवर्णसंधी असते. 💪", author: "डॉ. ए. पी. जे. अब्दुल कलाम" },
        { text: "हे फक्त माझं स्वप्न नाही, हे माझ्या आई-बाबांचे स्वप्न आहे! लक्षात ठेवा आणि अभ्यासाला लागा. ❤️", author: "एमपीएससी प्रेरणा" },
        { text: "तुमचा आजचा संघर्ष तुमचे उद्याचे सामर्थ्य निर्माण करतो. लढत राहा! 🔥", author: "स्वामी विवेकानंद" },
        { text: "स्वप्न ते नसतात जे आपण झोपेत पाहतो, स्वप्न ते असतात जे आपल्याला झोपू देत नाहीत. 🌟", author: "डॉ. ए. पी. जे. अब्दुल कलाम" },
        { text: "यशाचा कोणताही शॉर्टकट नसतो, त्यासाठी सातत्यपूर्ण कष्टाचीच गरज असते. 📖", author: "मार्गदर्शक" }
    ];

    // Get today's quote based on date
    const day = new Date().getDate();
    const selectedQuote = quotes[day % quotes.length];
    
    const quoteTextEl = document.getElementById('motivationalQuoteText');
    const quoteAuthorEl = document.querySelector('.motivation-section cite');
    
    if (quoteTextEl) quoteTextEl.textContent = `"${selectedQuote.text}"`;
    if (quoteAuthorEl) quoteAuthorEl.textContent = "— मार्गदर्शक Prajakta Lotake(MPSC Aspirant)";

    // Read streak from stats
    const stats = JSON.parse(localStorage.getItem('talathi_stats')) || { streak: 5 };
    const streakDaysCount = document.getElementById('streakDaysCount');
    if (streakDaysCount) streakDaysCount.textContent = stats.streak;

    // Get today's daily progress
    if (typeof getDailyProgress === 'function') {
        const progress = getDailyProgress();
        
        const mcqSolved = progress.questionsSolved || 0;
        const mockTaken = progress.mockTestsTaken || 0;
        const timeSpent = progress.timeSpentSeconds || 0;

        const mcqTarget = 10;
        const mockTarget = 1;
        const timeTargetSeconds = 600; // 10 minutes

        // Update MCQ progress
        const chkMcqProgress = document.getElementById('chkMcqProgress');
        const chkMcqIcon = document.getElementById('chkMcqIcon');
        if (chkMcqProgress) chkMcqProgress.textContent = `${mcqSolved} / ${mcqTarget}`;
        if (chkMcqIcon) {
            if (mcqSolved >= mcqTarget) {
                chkMcqIcon.innerHTML = '<i class="fas fa-check-circle" style="color: var(--success);"></i>';
                chkMcqProgress.style.color = 'var(--success)';
            } else {
                chkMcqIcon.innerHTML = '<i class="far fa-circle" style="color: var(--text-muted); font-size: 1rem;"></i>';
                chkMcqProgress.style.color = '';
            }
        }

        // Update Mock progress
        const chkMockProgress = document.getElementById('chkMockProgress');
        const chkMockIcon = document.getElementById('chkMockIcon');
        if (chkMockProgress) chkMockProgress.textContent = `${mockTaken} / ${mockTarget}`;
        if (chkMockIcon) {
            if (mockTaken >= mockTarget) {
                chkMockIcon.innerHTML = '<i class="fas fa-check-circle" style="color: var(--success);"></i>';
                chkMockProgress.style.color = 'var(--success)';
            } else {
                chkMockIcon.innerHTML = '<i class="far fa-circle" style="color: var(--text-muted); font-size: 1rem;"></i>';
                chkMockProgress.style.color = '';
            }
        }

        // Update Time progress
        const chkTimeProgress = document.getElementById('chkTimeProgress');
        const chkTimeIcon = document.getElementById('chkTimeIcon');
        const timeSpentMins = timeSpent / 60;
        const timeTargetMins = timeTargetSeconds / 60;
        if (chkTimeProgress) chkTimeProgress.textContent = `${timeSpentMins.toFixed(1)}m / ${timeTargetMins.toFixed(1)}m`;
        if (chkTimeIcon) {
            if (timeSpent >= timeTargetSeconds) {
                chkTimeIcon.innerHTML = '<i class="fas fa-check-circle" style="color: var(--success);"></i>';
                chkTimeProgress.style.color = 'var(--success)';
            } else {
                chkTimeIcon.innerHTML = '<i class="far fa-circle" style="color: var(--text-muted); font-size: 1rem;"></i>';
                chkTimeProgress.style.color = '';
            }
        }

        // Check if all completed
        const statusMsgEl = document.getElementById('motivationStatusMessage');
        if (statusMsgEl) {
            statusMsgEl.style.display = 'block';
            if (mcqSolved >= mcqTarget && mockTaken >= mockTarget && timeSpent >= timeTargetSeconds) {
                statusMsgEl.innerHTML = '🎉 आजचे ध्येय पूर्ण झाले! तुम्ही यशाच्या आणखी एक पाऊल जवळ आहात! 🚀';
                statusMsgEl.style.background = 'rgba(16, 185, 129, 0.1)';
                statusMsgEl.style.border = '1px solid rgba(16, 185, 129, 0.2)';
                statusMsgEl.style.color = 'var(--success)';
            } else {
                statusMsgEl.innerHTML = '🎯 आजचे ध्येय पूर्ण करण्यासाठी वरील कार्ये पूर्ण करा.';
                statusMsgEl.style.background = 'rgba(99, 102, 241, 0.05)';
                statusMsgEl.style.border = '1px dashed rgba(99, 102, 241, 0.2)';
                statusMsgEl.style.color = 'var(--text-muted)';
            }
        }
    }
}

