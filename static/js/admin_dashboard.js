// Enhanced Admin Dashboard JavaScript - FIXED VERSION
class AdminDashboard {
    constructor() {
        this.charts = {};
        this.data = {};
        this.refreshInterval = 30000;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.setupAutoRefresh();
        this.initializeCharts();
    }

    setupEventListeners() {
        // Quick action buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-action-btn')) {
                this.handleQuickAction(e.target);
            }
            
            if (e.target.classList.contains('refresh-btn')) {
                this.loadDashboardData();
            }
        });

        // Notification bell
        const notificationBell = document.getElementById('notification-bell');
        if (notificationBell) {
            notificationBell.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleNotifications();
            });
        }
    }

    initializeCharts() {
        // Only initialize charts if we're on a page that needs them
        this.createSalesChart();
        // Removed createRevenueChart and createCustomerChart since they don't exist
    }

    createSalesChart() {
        const ctx = document.getElementById('sales-chart');
        if (!ctx) return;

        this.charts.sales = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Sales ($)',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                }
            }
        });
    }

    async loadDashboardData() {
        try {
            this.showLoadingState();
            
            const [stats, notifications] = await Promise.all([
                this.apiCall('/admin-dashboard/api/stats/'),
                this.apiCall('/admin-dashboard/api/notifications/')
            ]);

            this.data = { stats, notifications };
            this.updateDashboardUI();
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.hideLoadingState();
        }
    }

    updateDashboardUI() {
        // Update stats cards
        this.updateStatCard('total-orders', this.data.stats.total_orders);
        this.updateStatCard('total-revenue', this.data.stats.total_revenue, true);
        this.updateStatCard('total-customers', this.data.stats.total_customers);
        this.updateStatCard('pending-orders', this.data.stats.pending_orders);

        // Update notifications
        this.updateNotifications();
    }

    updateStatCard(elementId, value, isCurrency = false) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = isCurrency ? this.formatCurrency(value) : this.formatNumber(value);
        }
    }

    updateNotifications() {
        const countElement = document.getElementById('notification-count');
        const listElement = document.getElementById('notification-list');
        
        if (countElement && this.data.notifications) {
            if (this.data.notifications.length > 0) {
                countElement.textContent = this.data.notifications.length;
                countElement.classList.remove('hidden');
            } else {
                countElement.classList.add('hidden');
            }
        }

        if (listElement && this.data.notifications) {
            if (this.data.notifications.length === 0) {
                listElement.innerHTML = '<div class="px-4 py-3 text-gray-500 text-center">No new notifications</div>';
            } else {
                listElement.innerHTML = this.data.notifications.map(notif => `
                    <div class="px-4 py-3 border-b hover:bg-gray-50 cursor-pointer">
                        <div class="flex justify-between items-start">
                            <span class="font-semibold text-sm">${notif.title}</span>
                            <span class="text-xs text-gray-500">${new Date(notif.created_at).toLocaleTimeString()}</span>
                        </div>
                        <p class="text-sm text-gray-600 mt-1">${notif.message}</p>
                    </div>
                `).join('');
            }
        }
    }

    toggleNotifications() {
        const dropdown = document.getElementById('notification-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('hidden');
        }
    }

    async handleQuickAction(button) {
        const action = button.dataset.action;
        const targetId = button.dataset.targetId;

        try {
            let result;
            switch (action) {
                case 'verify-user':
                    result = await this.verifyUser(targetId);
                    break;
                case 'update-order-status':
                    const newStatus = prompt('Enter new status:');
                    if (newStatus) {
                        result = await this.updateOrderStatus(targetId, newStatus);
                    }
                    break;
            }

            if (result) {
                this.showToast('Action completed successfully', 'success');
            }
        } catch (error) {
            this.showToast('Action failed: ' + error.message, 'error');
        }
    }

    // API methods
    async apiCall(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
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
            throw error;
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    async updateOrderStatus(orderId, newStatus) {
        const response = await this.apiCall(`/admin-dashboard/api/orders/update-status/${orderId}/`, {
            method: 'POST',
            body: JSON.stringify({ status: newStatus })
        });
        return response.success;
    }

    async verifyUser(userId) {
        const response = await this.apiCall(`/admin-dashboard/api/users/verify/${userId}/`, {
            method: 'POST'
        });
        return response.success;
    }

    // Utility methods
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    formatNumber(number) {
        return new Intl.NumberFormat('en-US').format(number);
    }

    showLoadingState() {
        // Implement loading states if needed
    }

    hideLoadingState() {
        // Implement loading states if needed
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        // Use the existing toast function from base.html
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    setupAutoRefresh() {
        setInterval(() => {
            this.loadDashboardData();
        }, this.refreshInterval);
    }
}

// Initialize only if we're on an admin dashboard page
if (document.querySelector('body.bg-gray-100')) {
    document.addEventListener('DOMContentLoaded', function() {
        window.adminDashboard = new AdminDashboard();
    });
}