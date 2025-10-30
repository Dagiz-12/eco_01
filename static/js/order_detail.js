class OrderDetailManager {
    constructor() {
        this.orderId = this.getOrderIdFromURL();
        this.orderData = null;
        console.log('OrderDetailManager initialized with order ID:', this.orderId);
        this.init();
    }

    getOrderIdFromURL() {
        const path = window.location.pathname;
        const matches = path.match(/\/orders\/(\d+)\//);
        const orderId = matches ? matches[1] : null;
        console.log('Extracted order ID from URL:', orderId);
        return orderId;
    }

    async init() {
        if (this.orderId) {
            await this.loadOrderDetails();
        } else {
            console.error('No order ID found in URL');
            this.showError('Order not found. Please check the URL.');
        }
    }

    async loadOrderDetails() {
        try {
            const apiUrl = `/api/orders/${this.orderId}/`;
            console.log('Fetching order details from:', apiUrl);
            
            const response = await fetch(apiUrl, {
                credentials: 'include' // Include cookies for authentication
            });
            
            console.log('API Response status:', response.status);
            
            if (response.ok) {
                this.orderData = await response.json();
                console.log('Order data received:', this.orderData);
                
                // Validate data structure
                if (!this.orderData || typeof this.orderData !== 'object') {
                    throw new Error('Invalid order data received');
                }
                
                this.renderOrderDetails();
            } else if (response.status === 401) {
                this.showError('Please log in to view this order');
            } else if (response.status === 403) {
                this.showError('You do not have permission to view this order');
            } else if (response.status === 404) {
                this.showError('Order not found');
            } else {
                this.showError(`Failed to load order details (Status: ${response.status})`);
            }
        } catch (error) {
            console.error('Error loading order details:', error);
            this.showError('Error loading order details: ' + error.message);
        }
    }

    renderOrderDetails() {
        if (!this.orderData) {
            this.showError('No order data available');
            return;
        }

        // Update order number
        const orderNumberElement = document.getElementById('order-number');
        if (orderNumberElement) {
            orderNumberElement.textContent = this.orderData.order_number || 'Unknown';
        }

        // Render all sections
        this.renderOrderInfo();
        this.renderOrderItems();
        this.renderAddresses();
        this.renderOrderSummary();
    }

    renderOrderInfo() {
        const container = document.getElementById('order-details');
        if (!container) {
            console.error('Order details container not found');
            return;
        }

        const statusColors = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'confirmed': 'bg-blue-100 text-blue-800',
            'processing': 'bg-purple-100 text-purple-800',
            'shipped': 'bg-indigo-100 text-indigo-800',
            'delivered': 'bg-green-100 text-green-800',
            'cancelled': 'bg-red-100 text-red-800',
            'refunded': 'bg-gray-100 text-gray-800'
        };

        const paymentStatusColors = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'paid': 'bg-green-100 text-green-800',
            'failed': 'bg-red-100 text-red-800',
            'refunded': 'bg-gray-100 text-gray-800',
            'cancelled': 'bg-red-100 text-red-800'
        };

        const order = this.orderData;
        
        container.innerHTML = `
            <div class="flex justify-between">
                <span class="text-gray-600">Order Number:</span>
                <span class="font-semibold">${order.order_number || 'N/A'}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-600">Order Date:</span>
                <span>${order.created_at ? new Date(order.created_at).toLocaleDateString() : 'N/A'}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-600">Status:</span>
                <span class="capitalize px-3 py-1 rounded-full text-sm ${statusColors[order.status] || 'bg-gray-100 text-gray-800'}">
                    ${order.status || 'unknown'}
                </span>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-600">Payment Status:</span>
                <span class="capitalize px-3 py-1 rounded-full text-sm ${paymentStatusColors[order.payment_status] || 'bg-gray-100 text-gray-800'}">
                    ${order.payment_status || 'unknown'}
                </span>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-600">Payment Method:</span>
                <span class="capitalize">${order.payment_method ? order.payment_method.replace(/_/g, ' ') : 'N/A'}</span>
            </div>
            ${order.tracking_number ? `
            <div class="flex justify-between">
                <span class="text-gray-600">Tracking Number:</span>
                <span class="font-mono">${order.tracking_number}</span>
            </div>
            ` : ''}
        `;
    }

    renderOrderItems() {
        const container = document.getElementById('order-items');
        if (!container) {
            console.error('Order items container not found');
            return;
        }

        const items = this.orderData.items || [];
        console.log('Rendering order items:', items);

        if (items.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">No items found in this order</p>';
            return;
        }

        container.innerHTML = items.map(item => {
            const productName = item.product?.name || item.product_name || 'Product';
            const variantName = item.variant?.name || item.variant_name;
            const quantity = item.quantity || 0;
            const price = parseFloat(item.price || 0).toFixed(2);
            const lineTotal = parseFloat(item.line_total || item.price * quantity || 0).toFixed(2);

            return `
                <div class="flex items-center justify-between py-4 border-b">
                    <div class="flex items-center space-x-4 flex-1">
                        <div class="w-16 h-16 bg-gray-200 rounded flex items-center justify-center">
                            <i class="fas fa-image text-gray-400"></i>
                        </div>
                        <div class="flex-1">
                            <h3 class="font-semibold">${productName}</h3>
                            ${variantName ? `<p class="text-sm text-gray-600">${variantName}</p>` : ''}
                            <p class="text-sm text-gray-600">Quantity: ${quantity}</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="font-semibold">$${lineTotal}</p>
                        <p class="text-sm text-gray-600">$${price} each</p>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderAddresses() {
        this.renderAddress(this.orderData.shipping_address, 'shipping');
        this.renderAddress(this.orderData.billing_address, 'billing');
    }

    renderAddress(addressData, type) {
        const container = document.getElementById(`${type}-address`);
        if (!container) {
            console.error(`${type} address container not found`);
            return;
        }

        if (!addressData) {
            container.innerHTML = `<p class="text-gray-500">No ${type} address available</p>`;
            return;
        }

        container.innerHTML = `
            <p class="font-semibold">${addressData.street || 'N/A'}</p>
            <p class="text-gray-600">${addressData.city || ''}, ${addressData.state || ''} ${addressData.zip_code || ''}</p>
            <p class="text-gray-600">${addressData.country || ''}</p>
        `;
    }

    renderOrderSummary() {
        const subtotal = parseFloat(this.orderData.subtotal || 0).toFixed(2);
        const shipping = parseFloat(this.orderData.shipping_cost || 0).toFixed(2);
        const tax = parseFloat(this.orderData.tax_amount || 0).toFixed(2);
        const total = parseFloat(this.orderData.grand_total || 0).toFixed(2);

        document.getElementById('order-subtotal').textContent = `$${subtotal}`;
        document.getElementById('order-shipping').textContent = `$${shipping}`;
        document.getElementById('order-tax').textContent = `$${tax}`;
        document.getElementById('order-total').textContent = `$${total}`;
    }

    showError(message) {
        // Show error in order details section
        const container = document.getElementById('order-details');
        if (container) {
            container.innerHTML = `
                <div class="text-center py-8 text-red-600">
                    <i class="fas fa-exclamation-triangle text-3xl mb-2"></i>
                    <p class="font-semibold">${message}</p>
                    <p class="text-sm mt-2">Please try refreshing the page or contact support if the problem persists.</p>
                </div>
            `;
        }
        
        // Also show a toast notification
        if (typeof showToast !== 'undefined') {
            showToast(message, 'error');
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing OrderDetailManager...');
    new OrderDetailManager();
});