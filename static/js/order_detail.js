// static/js/order_detail.js
class OrderDetailManager {
    constructor(orderId) {
        this.orderId = orderId;
        this.init();
    }

    async init() {
        await this.loadOrderData();
        this.setupEventListeners();
    }

    async loadOrderData() {
        try {
            console.log(`Loading order data for order ID: ${this.orderId}`);
            console.log(`API Endpoint: /api/orders/${this.orderId}/`);
            
            const response = await fetch(`/api/orders/${this.orderId}/`);
            
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get("content-type");
            console.log('Content-Type:', contentType);
            
            if (!contentType || !contentType.includes("application/json")) {
                const textResponse = await response.text();
                console.error('Non-JSON response received:', textResponse.substring(0, 500));
                throw new Error("Response is not JSON. Received: " + contentType);
            }

            const data = await response.json();
            console.log('Order data loaded successfully:', data);
            this.renderOrderData(data);
            
        } catch (error) {
            console.error('Error loading order details:', error);
            this.showError('Failed to load order details: ' + error.message);
        }
    }

    renderOrderData(orderData) {
        // Update order number
        document.getElementById('order-number').textContent = orderData.order_number;
        
        // Render order details
        this.renderOrderDetails(orderData);
        
        // Render order items
        this.renderOrderItems(orderData.items || []);
        
        // Render addresses
        this.renderAddresses(orderData);
        
        // Render order summary
        this.renderOrderSummary(orderData);
    }

    renderOrderDetails(orderData) {
        const container = document.getElementById('order-details');
        if (!container) return;

        const statusColors = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'confirmed': 'bg-blue-100 text-blue-800',
            'processing': 'bg-purple-100 text-purple-800',
            'shipped': 'bg-indigo-100 text-indigo-800',
            'delivered': 'bg-green-100 text-green-800',
            'cancelled': 'bg-red-100 text-red-800'
        };

        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <p class="text-sm text-gray-600">Order Number</p>
                    <p class="font-semibold">${orderData.order_number}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-600">Order Date</p>
                    <p class="font-semibold">${new Date(orderData.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-600">Status</p>
                    <span class="inline-block px-3 py-1 rounded-full text-sm font-semibold ${statusColors[orderData.status] || 'bg-gray-100 text-gray-800'}">
                        ${orderData.status.charAt(0).toUpperCase() + orderData.status.slice(1)}
                    </span>
                </div>
                <div>
                    <p class="text-sm text-gray-600">Payment Status</p>
                    <span class="inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                        orderData.payment_status === 'paid' ? 'bg-green-100 text-green-800' : 
                        orderData.payment_status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                        'bg-red-100 text-red-800'
                    }">
                        ${orderData.payment_status.charAt(0).toUpperCase() + orderData.payment_status.slice(1)}
                    </span>
                </div>
                <div>
                    <p class="text-sm text-gray-600">Payment Method</p>
                    <p class="font-semibold">${this.formatPaymentMethod(orderData.payment_method)}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-600">Shipping Method</p>
                    <p class="font-semibold">Standard Shipping</p>
                </div>
            </div>
        `;
    }

    renderOrderItems(items) {
        const container = document.getElementById('order-items');
        if (!container) return;

        if (items.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-shopping-bag text-4xl text-gray-300 mb-4"></i>
                    <p class="text-gray-600">No items in this order</p>
                </div>
            `;
            return;
        }

        container.innerHTML = items.map(item => {
            // FIXED: Parse price as number and handle null/undefined
            const price = parseFloat(item.price) || 0;
            const quantity = parseInt(item.quantity) || 0;
            const totalPrice = price * quantity;

            return `
            <div class="flex items-center justify-between py-4 border-b">
                <div class="flex items-center space-x-4">
                    <div class="w-16 h-16 bg-gray-200 rounded flex items-center justify-center">
                        ${item.product?.images?.[0] ? 
                            `<img src="${item.product.images[0]}" alt="${item.product.name}" class="w-full h-full object-cover rounded">` :
                            `<i class="fas fa-image text-gray-400"></i>`
                        }
                    </div>
                    <div class="flex-1">
                        <h3 class="font-semibold">${item.product?.name || 'Product'}</h3>
                        ${item.variant ? `<p class="text-sm text-gray-600">${item.variant.name}</p>` : ''}
                        <p class="text-sm text-gray-600">Quantity: ${quantity}</p>
                        <p class="text-sm text-gray-600">SKU: ${item.product?.sku || 'N/A'}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="font-semibold">$${totalPrice.toFixed(2)}</p>
                    <p class="text-sm text-gray-600">$${price.toFixed(2)} each</p>
                </div>
            </div>
            `;
        }).join('');
    }

    renderAddresses(orderData) {
        const shippingContainer = document.getElementById('shipping-address');
        const billingContainer = document.getElementById('billing-address');

        if (orderData.shipping_address) {
            shippingContainer.innerHTML = this.formatAddress(orderData.shipping_address);
        } else {
            shippingContainer.innerHTML = `
                <div class="text-center py-4 text-gray-500">
                    <i class="fas fa-map-marker-alt mb-2"></i>
                    <p>No shipping address provided</p>
                </div>
            `;
        }

        if (orderData.billing_address) {
            billingContainer.innerHTML = this.formatAddress(orderData.billing_address);
        } else {
            billingContainer.innerHTML = `
                <div class="text-center py-4 text-gray-500">
                    <i class="fas fa-receipt mb-2"></i>
                    <p>No billing address provided</p>
                </div>
            `;
        }
    }

    formatAddress(address) {
        return `
            <div class="space-y-1">
                <p class="font-semibold">${address.street}</p>
                <p class="text-gray-600">${address.city}, ${address.state} ${address.zip_code}</p>
                <p class="text-gray-600">${address.country}</p>
                ${address.phone ? `<p class="text-gray-600">Phone: ${address.phone}</p>` : ''}
            </div>
        `;
    }

    renderOrderSummary(orderData) {
        // FIXED: Parse all numeric values
        const subtotal = parseFloat(orderData.subtotal) || 0;
        const shippingCost = parseFloat(orderData.shipping_cost) || 0;
        const taxAmount = parseFloat(orderData.tax_amount) || 0;
        const grandTotal = parseFloat(orderData.grand_total) || 0;

        document.getElementById('order-subtotal').textContent = `$${subtotal.toFixed(2)}`;
        document.getElementById('order-shipping').textContent = `$${shippingCost.toFixed(2)}`;
        document.getElementById('order-tax').textContent = `$${taxAmount.toFixed(2)}`;
        document.getElementById('order-total').textContent = `$${grandTotal.toFixed(2)}`;
    }

    formatPaymentMethod(method) {
        const methods = {
            'stripe': 'Credit/Debit Card',
            'paypal': 'PayPal',
            'cbe': 'CBE Birr',
            'telebirr': 'TeleBirr'
        };
        return methods[method] || method.charAt(0).toUpperCase() + method.slice(1);
    }

    showError(message) {
        const containers = [
            'order-details',
            'order-items',
            'shipping-address',
            'billing-address'
        ];

        containers.forEach(containerId => {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-4 text-red-600">
                        <i class="fas fa-exclamation-triangle mb-2"></i>
                        <p>${message}</p>
                    </div>
                `;
            }
        });
    }

    setupEventListeners() {
        // Add any event listeners needed
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    let orderId = null;
    
    // Method 1: Use the global ORDER_ID from template
    if (typeof ORDER_ID !== 'undefined' && ORDER_ID) {
        orderId = ORDER_ID;
        console.log('Using ORDER_ID from template:', orderId);
    }
    // Method 2: Extract from URL
    else {
        const urlParts = window.location.pathname.split('/');
        console.log('URL parts:', urlParts);
        
        // Handle both URL patterns: /orders/11/ and /orders/11/detail/
        for (let i = 0; i < urlParts.length; i++) {
            const part = urlParts[i];
            if (part && !isNaN(part) && i > 0 && urlParts[i-1] === 'orders') {
                orderId = part;
                break;
            }
        }
        console.log('Extracted order ID from URL:', orderId);
    }
    
    // Method 3: Get from data attribute
    if (!orderId) {
        const orderIdElement = document.getElementById('order-id-data');
        if (orderIdElement) {
            orderId = orderIdElement.dataset.orderId;
            console.log('Using order ID from data attribute:', orderId);
        }
    }
    
    if (orderId && !isNaN(orderId)) {
        console.log('Initializing order detail manager for order:', orderId);
        window.orderDetailManager = new OrderDetailManager(parseInt(orderId));
    } else {
        console.error('Could not extract order ID from URL. Path:', window.location.pathname);
        // Show error to user
        const errorContainers = document.querySelectorAll('#order-details, #order-items, #shipping-address, #billing-address');
        errorContainers.forEach(container => {
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-8 text-red-600">
                        <i class="fas fa-exclamation-triangle text-3xl mb-4"></i>
                        <p>Could not load order details. Invalid order ID.</p>
                        <a href="/orders/" class="text-blue-600 hover:underline mt-2 inline-block">
                            View All Orders
                        </a>
                    </div>
                `;
            }
        });
    }
});