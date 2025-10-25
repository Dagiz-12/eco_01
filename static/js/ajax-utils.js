class AjaxUtils {
    constructor() {
        this.csrfToken = this.getCSRFToken();
        this.setupAjaxDefaults();
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        return csrfToken ? csrfToken.getAttribute('content') : '';
    }

    setupAjaxDefaults() {
        // Set up axios defaults
        if (typeof axios !== 'undefined') {
            axios.defaults.xsrfHeaderName = "X-CSRFToken";
            axios.defaults.xsrfCookieName = "csrftoken";
        }
    }

    async makeRequest(url, method = 'GET', data = null, options = {}) {
        const config = {
            method: method,
            url: url,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            },
            ...options
        };

        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            config.data = data;
        }

        try {
            const response = await axios(config);
            return {
                success: true,
                data: response.data,
                status: response.status
            };
        } catch (error) {
            console.error('AJAX Request failed:', error);
            return {
                success: false,
                error: error.response?.data || error.message,
                status: error.response?.status || 500
            };
        }
    }

    showMessage(message, type = 'success', duration = 5000) {
        const messagesContainer = document.getElementById('messages-container');
        if (!messagesContainer) return;

        const messageEl = document.createElement('div');
        messageEl.className = `message ${type} p-4 rounded-lg shadow-lg transform transition-all duration-300`;
        
        const bgColor = type === 'success' ? 'bg-green-500' : 
                       type === 'error' ? 'bg-red-500' : 
                       type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500';
        
        messageEl.className += ` ${bgColor} text-white`;
        messageEl.innerHTML = `
            <div class="flex justify-between items-center">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        messagesContainer.appendChild(messageEl);

        // Auto remove after duration
        setTimeout(() => {
            if (messageEl.parentElement) {
                messageEl.remove();
            }
        }, duration);
    }

    showLoading(element, text = 'Loading...') {
        if (element) {
            element.disabled = true;
            const originalText = element.innerHTML;
            element.innerHTML = `
                <i class="fas fa-spinner fa-spin mr-2"></i>
                ${text}
            `;
            element.setAttribute('data-original-text', originalText);
        }
    }

    hideLoading(element) {
        if (element && element.hasAttribute('data-original-text')) {
            element.disabled = false;
            element.innerHTML = element.getAttribute('data-original-text');
            element.removeAttribute('data-original-text');
        }
    }

    updateCounter(counterId, count) {
        const counter = document.getElementById(counterId);
        if (counter) {
            counter.textContent = count;
            
            // Add animation
            counter.classList.add('counter-update');
            setTimeout(() => {
                counter.classList.remove('counter-update');
            }, 300);
        }
    }

    // Form handling
    async submitForm(formElement, options = {}) {
        const formData = new FormData(formElement);
        const url = formElement.action;
        const method = formElement.method || 'POST';

        this.showLoading(formElement.querySelector('button[type="submit"]'));

        try {
            const response = await this.makeRequest(url, method, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                }
            });

            if (response.success) {
                this.showMessage(options.successMessage || 'Operation completed successfully!');
                if (options.onSuccess) {
                    options.onSuccess(response.data);
                }
            } else {
                this.showMessage(options.errorMessage || 'Operation failed!', 'error');
                if (options.onError) {
                    options.onError(response.error);
                }
            }
        } finally {
            this.hideLoading(formElement.querySelector('button[type="submit"]'));
        }
    }

    // Real-time updates
    setupWebSocket() {
        // WebSocket setup for real-time features
        if (typeof WebSocket !== 'undefined') {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/notifications/`;
            
            try {
                const ws = new WebSocket(wsUrl);
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                };
                
                ws.onclose = () => {
                    console.log('WebSocket connection closed');
                    // Attempt reconnect after 5 seconds
                    setTimeout(() => this.setupWebSocket(), 5000);
                };
            } catch (error) {
                console.error('WebSocket connection failed:', error);
            }
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'notification':
                this.updateCounter('notification-count', data.count);
                this.showMessage(data.message, 'info');
                break;
            case 'cart_update':
                this.updateCounter('cart-count', data.count);
                break;
            case 'wishlist_update':
                this.updateCounter('wishlist-count', data.count);
                break;
        }
    }
}

// Global instance
const ajaxUtils = new AjaxUtils();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ajaxUtils.setupWebSocket();
    
    // Load initial counts
    ajaxUtils.loadInitialCounts();
});

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AjaxUtils;
}