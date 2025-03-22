document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const darkIcon = document.getElementById('dark-icon');
    const lightIcon = document.getElementById('light-icon');
    
    // Check for saved user preference in localStorage
    const prefersDarkMode = localStorage.getItem('darkMode') === 'true';
    
    // Initialize dark mode based on saved preference
    if (prefersDarkMode) {
        enableDarkMode();
    }
    
    // Toggle dark mode on button click
    darkModeToggle.addEventListener('click', () => {
        if (document.body.classList.contains('dark-mode')) {
            disableDarkMode();
        } else {
            enableDarkMode();
        }
    });
    
    // Enable dark mode function
    function enableDarkMode() {
        document.body.classList.add('dark-mode');
        darkIcon.classList.add('d-none');
        lightIcon.classList.remove('d-none');
        localStorage.setItem('darkMode', 'true');
    }
    
    // Disable dark mode function
    function disableDarkMode() {
        document.body.classList.remove('dark-mode');
        darkIcon.classList.remove('d-none');
        lightIcon.classList.add('d-none');
        localStorage.setItem('darkMode', 'false');
    }
});