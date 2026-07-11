/**
 * Theme Manager - Handles dark/light mode switching
 */

const ThemeManager = {
    STORAGE_KEY: 'codecompass_theme',
    LIGHT_MODE_CLASS: 'light-mode',
    DARK_MODE_CLASS: 'dark-mode',

    /**
     * Initialize theme from localStorage or system preference
     */
    init() {
        const savedTheme = this.getSavedTheme();
        if (savedTheme) {
            this.setTheme(savedTheme);
        } else {
            // Use system preference if no saved theme
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.setTheme(prefersDark ? 'dark' : 'light');
        }
        this.createThemeToggleButton();
    },

    /**
     * Get saved theme from localStorage
     */
    getSavedTheme() {
        return localStorage.getItem(this.STORAGE_KEY);
    },

    /**
     * Get current theme (from DOM)
     */
    getCurrentTheme() {
        if (document.documentElement.classList.contains(this.LIGHT_MODE_CLASS)) {
            return 'light';
        }
        return 'dark';
    },

    /**
     * Set theme to light or dark
     */
    setTheme(theme) {
        const html = document.documentElement;

        if (theme === 'light') {
            html.classList.add(this.LIGHT_MODE_CLASS);
            html.classList.remove(this.DARK_MODE_CLASS);
        } else {
            html.classList.remove(this.LIGHT_MODE_CLASS);
            html.classList.add(this.DARK_MODE_CLASS);
        }

        // Save to localStorage
        localStorage.setItem(this.STORAGE_KEY, theme);

        // Update toggle button if exists
        this.updateToggleButton(theme);
    },

    /**
     * Toggle between light and dark mode
     */
    toggle() {
        const current = this.getCurrentTheme();
        const newTheme = current === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    },

    /**
     * Create and inject theme toggle button into navbar or top-bar
     */
    createThemeToggleButton() {
        // Check if button already exists
        if (document.getElementById('theme-toggle-btn')) {
            return;
        }

        // Try to find appropriate container (topbar for dashboard, navbar for landing)
        const topBar = document.querySelector('.top-bar') || document.querySelector('.navbar');
        if (!topBar) return;

        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'theme-toggle-btn';
        toggleBtn.type = 'button';
        toggleBtn.className = 'theme-toggle-btn';
        toggleBtn.setAttribute('aria-label', 'Toggle dark/light mode');
        toggleBtn.innerHTML = this.getCurrentTheme() === 'dark' 
            ? '☀️ Light' 
            : '🌙 Dark';

        // Add click listener
        toggleBtn.addEventListener('click', () => this.toggle());

        // Find the right place to insert
        const newProjectBtn = topBar.querySelector('.new-project-btn');
        const authBtn = topBar.querySelector('.auth-btn, .logout-btn, [href*=login], [href*=signup]');
        
        if (newProjectBtn) {
            // Dashboard layout - insert before new project button
            newProjectBtn.parentNode.insertBefore(toggleBtn, newProjectBtn);
        } else if (authBtn) {
            // Landing page with auth - insert before auth buttons
            authBtn.parentNode.insertBefore(toggleBtn, authBtn);
        } else {
            // Fallback - just append to navbar
            topBar.appendChild(toggleBtn);
        }
    },

    /**
     * Update toggle button text and icon
     */
    updateToggleButton(theme) {
        const toggleBtn = document.getElementById('theme-toggle-btn');
        if (toggleBtn) {
            toggleBtn.innerHTML = theme === 'dark' 
                ? '☀️ Light' 
                : '🌙 Dark';
        }
    }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => ThemeManager.init());
} else {
    ThemeManager.init();
}
