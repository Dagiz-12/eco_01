// static/js/order_list.js
class OrderListManager {
    constructor() {
        this.orders = [];
        this.init();
    }

    async init() {
        await this.loadOrders();
        this.setupEventListeners();
    }

    async loadOrders() {
        try {
            console.log('Loading orders...');
            
            const response = await fetch('/api/orders/');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Orders loaded:', data);
            
            if (Array.isArray(data)) {
                this.orders = data;
                this.renderOrders();
            } else if (data.results && Array.isArray(data.results)) {
                this.orders = data.results;
                this.renderOrders();
            } else {
                throw new Error('Invalid orders data format');
            }
            
        } catch (error) {
            console.error('Error loading orders:', error);
            this.showError('Failed to load orders: ' + error.message);
        }
    }

    renderOrders() {
        const container = document.getElementById('orders-container');
        const emptyState = document.getElementById('empty-orders');

        if (!container) return;

        if (this.orders.length === 0) {
            container.classList.add('hidden');
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');
        container.classList.remove('hidden');

        container.innerHTML = this.orders.map(order => {
            const statusColor = this.getStatusColor(order.status);
            const itemCount = order.items ? order.items.length : 0;
            const orderDate = new Date(order.created_at).toLocaleDateString();
            const totalAmount = parseFloat(order.grand_total || order.total || 0).toFixed(2);

            return `
            <div class="border-b last:border-b-0">
                <div class="p-6 hover:bg-gray-50 transition-colors">
                    <div class="flex flex-col md:flex-row md:items-center md:justify-between">
                        <!-- Order Info -->
                        <div class="flex-1 mb-4 md:mb-0">
                            <div class="flex items-center space-x-4 mb-2">
                                <h3 class="text-lg font-semibold text-gray-800">
                                    Order #${order.order_number}
                                </h3>
                                <span class="inline-block px-3 py-1 rounded-full text-sm font-semibold ${statusColor}">
                                    ${order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                                </span>
                            </div>
                            
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                                <div>
                                    <span class="font-medium">Date:</span>
                                    <span>${orderDate}</span>
                                </div>
                                <div>
                                    <span class="font-medium">Items:</span>
                                    <span>${itemCount}</span>
                                </div>
                                <div>
                                    <span class="font-medium">Total:</span>
                                    <span class="font-semibold">$${totalAmount}</span>
                                </div>
                                <div>
                                    <span class="font-medium">Payment:</span>
                                    <span class="capitalize">${order.payment_status}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Actions -->
                        <div class="flex space-x-3">
                            <a href="/orders/${order.id}/" 
                               class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                                View Details
                            </a>
                            ${order.status === 'pending' ? `
                            <button onclick="orderListManager.cancelOrder(${order.id})" 
                                    class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm font-medium">
                                Cancel
                            </button>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Order Items Preview -->
                    ${order.items && order.items.length > 0 ? `
                    <div class="mt-4 pt-4 border-t">
                        <h4 class="text-sm font-medium text-gray-700 mb-2">Items:</h4>
                        <div class="flex flex-wrap gap-2">
                            ${order.items.slice(0, 3).map(item => `
                                <span class="bg-gray-100 px-2 py-1 rounded text-sm text-gray-600">
                                    ${item.product?.name || 'Product'} × ${item.quantity}
                                </span>
                            `).join('')}
                            ${order.items.length > 3 ? `
                                <span class="bg-gray-100 px-2 py-1 rounded text-sm text-gray-600">
                                    +${order.items.length - 3} more
                                </span>
                            ` : ''}
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
            `;
        }).join('');
    }

    getStatusColor(status) {
        const colors = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'confirmed': 'bg-blue-100 text-blue-800',
            'processing': 'bg-purple-100 text-purple-800',
            'shipped': 'bg-indigo-100 text-indigo-800',
            'delivered': 'bg-green-100 text-green-800',
            'cancelled': 'bg-red-100 text-red-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    }

    async cancelOrder(orderId) {
        if (!confirm('Are you sure you want to cancel this order?')) {
            return;
        }

        try {
            const response = await fetch(`/api/orders/${orderId}/cancel/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });

            if (response.ok) {
                showToast('Order cancelled successfully', 'success');
                // Reload orders to reflect the change
                await this.loadOrders();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to cancel order');
            }
        } catch (error) {
            console.error('Error cancelling order:', error);
            showToast('Failed to cancel order: ' + error.message, 'error');
        }
    }

    showError(message) {
        const container = document.getElementById('orders-container');
        if (container) {
            container.innerHTML = `
                <div class="text-center py-12 text-red-600">
                    <i class="fas fa-exclamation-triangle text-3xl mb-4"></i>
                    <h3 class="text-lg font-semibold mb-2">Failed to Load Orders</h3>
                    <p class="mb-4">${message}</p>
                    <button onclick="orderListManager.loadOrders()" 
                            class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors">
                        Try Again
                    </button>
                </div>
            `;
        }
    }

    setupEventListeners() {
        // Add any additional event listeners here
    }
}

// Initialize when DOM is loaded
let orderListManager;
document.addEventListener('DOMContentLoaded', function() {
    orderListManager = new OrderListManager();
});