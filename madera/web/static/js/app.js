// MADERA MCP - Global App JavaScript
// Vanilla JS - No frameworks!

// Global helpers
const App = {
    // API base URL
    apiBase: '/api',

    // Show toast notification
    toast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // Show loading overlay
    showLoading(message = 'Loading...') {
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-spinner"></div>
                <p id="loading-message">${message}</p>
            `;
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
        document.getElementById('loading-message').textContent = message;
    },

    // Hide loading overlay
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    },

    // Format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },

    // Format date
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-CA') + ' ' + date.toLocaleTimeString('fr-CA');
    },

    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
};

// Active nav link highlighting
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath ||
            (currentPath.startsWith(link.getAttribute('href')) && link.getAttribute('href') !== '/')) {
            link.classList.add('active');
        }
    });
});

// Global error handler
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

// Handle API errors
window.handleApiError = function(error) {
    console.error('API Error:', error);

    let message = 'An error occurred';

    if (error.response) {
        // Server responded with error
        message = error.response.data.detail || error.response.statusText;
    } else if (error.request) {
        // Request made but no response
        message = 'No response from server';
    } else {
        // Error in request setup
        message = error.message;
    }

    App.toast(message, 'error');
    App.hideLoading();
};

console.log('🤖 MADERA MCP Training UI - Ready');
