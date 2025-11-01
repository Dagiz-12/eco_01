// Admin Dashboard JavaScript Utilities
class AdminDashboard {
    constructor() {
        this.charts = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Add global event listeners for admin dashboard
    }

    loadInitialData() {
        // Load initial data for dashboard
    }

    // Chart management
    createChart(canvasId, config) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, config);
        return this.charts[canvasId];
    }

    // Data formatting utilities
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    formatNumber(number) {
        return new Intl.NumberFormat('en-US').format(number);
    }

    // API call wrapper
    async apiCall(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            showToast('Failed to load data: ' + error.message, 'error');
            throw error;
        }
    }

    // Quick actions
    async updateOrderStatus(orderId, newStatus) {
        try {
            const response = await this.apiCall(`/admin-dashboard/api/orders/update-status/${orderId}/`, {
                method: 'POST',
                body: JSON.stringify({ status: newStatus })
            });

            if (response.success) {
                showToast('Order status updated successfully', 'success');
                return true;
            }
        } catch (error) {
            showToast('Failed to update order status', 'error');
        }
        return false;
    }

    async verifyUser(userId) {
        try {
            const response = await this.apiCall(`/admin-dashboard/api/users/verify/${userId}/`, {
                method: 'POST'
            });

            if (response.success) {
                showToast('User verified successfully', 'success');
                return true;
            }
        } catch (error) {
            showToast('Failed to verify user', 'error');
        }
        return false;
    }
}

// Initialize admin dashboard
let adminDashboard;
document.addEventListener('DOMContentLoaded', function() {
    adminDashboard = new AdminDashboard();
});