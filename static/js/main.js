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

// Utility to helper format timing (MM:SS)
function formatTime(seconds) {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
}
