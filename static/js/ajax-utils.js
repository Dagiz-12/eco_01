class AjaxUtils {
    constructor() {
        this.csrfToken = this.getCSRFToken();
        this.setupAjaxDefaults();
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
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
                'X-CSRFToken': this.csrfToken
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

    showMessage(message, type = 'info') {
        // Use the new toast system instead of old alerts
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            // Fallback to old alert system
            alert(message);
        }
    }

    // Add this new method for consistency
    showToast(message, type = 'info', duration = 5000) {
        if (window.showToast) {
            return window.showToast(message, type, duration);
        }
        // Fallback
        this.showMessage(message, type);
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

    // Load initial counts
    async loadInitialCounts() {
    try {
        // ✅ CORRECT ENDPOINTS
        const cartResponse = await this.makeRequest('/api/cart/api/detail/');
        if (cartResponse.success) {
            this.updateCounter('cart-count', cartResponse.data.total_items || 0);
        }

        const wishlistResponse = await this.makeRequest('/api/wishlist/api/detail/');
        if (wishlistResponse.success) {
            this.updateCounter('wishlist-count', wishlistResponse.data.item_count || 0);
        }
    } catch (error) {
        console.error('Failed to load initial counts:', error);
    }
}
}

// ✅ SINGLE GLOBAL INSTANCE - Remove duplicates below this line
const ajaxUtils = new AjaxUtils();
window.ajaxUtils = ajaxUtils;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ajaxUtils.loadInitialCounts();
});