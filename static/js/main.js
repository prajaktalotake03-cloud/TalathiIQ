// Main scripts for TalathiIQ
document.addEventListener('DOMContentLoaded', () => {
    // Mobile Navigation Toggle
    const navToggle = document.getElementById('navToggle');
    const mobileMenu = document.getElementById('mobileMenu');

    if (navToggle && mobileMenu) {
        navToggle.addEventListener('click', () => {
            if (mobileMenu.style.display === 'flex') {
                mobileMenu.style.display = 'none';
                navToggle.innerHTML = '<i class="fas fa-bars"></i>';
            } else {
                mobileMenu.style.display = 'flex';
                navToggle.innerHTML = '<i class="fas fa-times"></i>';
            }
        });
    }

    // Dynamic Current Year in Footer
    const yearSpan = document.getElementById('currentYear');
    if (yearSpan) {
        yearSpan.textContent = new Date().getFullYear();
    }
});

// Utility helper to format timing (HH:MM:SS or MM:SS)
function formatTime(seconds) {
    if (seconds < 0) seconds = 0;
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return h > 0 ? `${h}:${m}:${s}` : `${m}:${s}`;
}

// Daily Target & Goal Progress Tracker
function getTodayDateString() {
    const d = new Date();
    return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`;
}

function getDailyProgress() {
    const today = getTodayDateString();
    let daily = JSON.parse(localStorage.getItem('talathi_daily_progress'));
    if (!daily || daily.date !== today) {
        daily = {
            date: today,
            questionsSolved: 0,
            mockTestsTaken: 0,
            timeSpentSeconds: 0
        };
        localStorage.setItem('talathi_daily_progress', JSON.stringify(daily));
    }
    return daily;
}

function saveDailyProgress(daily) {
    localStorage.setItem('talathi_daily_progress', JSON.stringify(daily));
}

function getDailyTargets() {
    let targets = JSON.parse(localStorage.getItem('talathi_daily_targets'));
    if (!targets) {
        targets = {
            questionsSolved: 50,
            mockTestsTaken: 1,
            timeSpentSeconds: 7200 // Default 2 hours in seconds
        };
        localStorage.setItem('talathi_daily_targets', JSON.stringify(targets));
    }
    return targets;
}

function saveDailyTargets(targets) {
    localStorage.setItem('talathi_daily_targets', JSON.stringify(targets));
}

function incrementDailyStat(key, amount = 1) {
    const daily = getDailyProgress();
    daily[key] = (daily[key] || 0) + amount;
    saveDailyProgress(daily);
}

// Run visibility-aware background timer to track active study session time
setInterval(() => {
    if (document.visibilityState === 'visible') {
        incrementDailyStat('timeSpentSeconds', 1);
    }
}, 1000);

