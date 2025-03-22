// Dark mode toggle button for navbar
document.addEventListener('DOMContentLoaded', function() {
    // Create the dark mode toggle
    createDarkModeToggle();
});

function createDarkModeToggle() {
    // Find the navbar-nav where we'll add the toggle
    const navbarNav = document.querySelector('.navbar-nav');
    if (!navbarNav) return;
    
    // Create a new list item for the toggle
    const toggleLi = document.createElement('li');
    toggleLi.className = 'nav-item ms-3 d-flex align-items-center';
    
    // Create the toggle switch HTML
    toggleLi.innerHTML = `
        <div class="form-check form-switch">
            <label class="form-check-label me-2 text-nowrap" for="darkModeToggle">
                <i class="fas fa-moon"></i>
            </label>
            <input class="form-check-input" type="checkbox" id="darkModeToggle">
        </div>
    `;
    
    // Append to navbar
    navbarNav.appendChild(toggleLi);
    
    // Initialize dark mode state
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        // Set initial state based on localStorage
        darkModeToggle.checked = localStorage.getItem('darkMode') === 'enabled';
        
        // Update body class to match initial state
        if (darkModeToggle.checked) {
            document.body.classList.add('dark-mode');
        }
    }
} 