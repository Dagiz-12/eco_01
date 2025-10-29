// static/js/toast.js
class ToastManager {
    constructor() {
        this.container = this.createToastContainer();
    }

    createToastContainer() {
        // Remove existing container if any
        const existing = document.getElementById('toast-container');
        if (existing) existing.remove();
        
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2 max-w-sm';
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `p-4 rounded-lg shadow-lg transform transition-all duration-300 ${this.getToastClasses(type)}`;
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="${this.getToastIcon(type)} mr-3"></i>
                <span class="flex-1">${message}</span>
                <button class="ml-4 text-gray-400 hover:text-gray-600 close-toast">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        this.container.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
        }, 10);

        // Close button event
        toast.querySelector('.close-toast').addEventListener('click', () => {
            this.removeToast(toast);
        });

        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                this.removeToast(toast);
            }, duration);
        }

        return toast;
    }

    getToastClasses(type) {
        const classes = {
            success: 'bg-green-50 text-green-800 border border-green-200',
            error: 'bg-red-50 text-red-800 border border-red-200',
            warning: 'bg-yellow-50 text-yellow-800 border border-yellow-200',
            info: 'bg-blue-50 text-blue-800 border border-blue-200'
        };
        return `${classes[type] || classes.info} translate-x-full opacity-0`;
    }

    getToastIcon(type) {
        const icons = {
            success: 'fas fa-check-circle text-green-500',
            error: 'fas fa-exclamation-circle text-red-500',
            warning: 'fas fa-exclamation-triangle text-yellow-500',
            info: 'fas fa-info-circle text-blue-500'
        };
        return icons[type] || icons.info;
    }

    removeToast(toast) {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    }
}

// Create single global instance
window.toastManager = new ToastManager();

// Global function for easy access
window.showToast = function(message, type = 'info', duration = 5000) {
    return toastManager.show(message, type, duration);
};