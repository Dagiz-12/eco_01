// Add this function at the TOP of checkout.js
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Make sure showToast function exists globally
if (typeof showToast === 'undefined') {
    function showToast(message, type = 'info') {
        const container = document.getElementById('messages-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `p-4 rounded-lg shadow-lg ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        toast.textContent = message;

        container.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
    window.showToast = showToast;
}

class CheckoutManager {
    constructor() {
        this.shippingAddressId = null;
        this.billingAddressId = null;
        this.paymentMethod = null;
        this.cartData = null;
        this.userAddresses = [];
        
        this.init();
    }

    async init() {
        await this.loadCartData();
        await this.loadAddresses();
        await this.loadPaymentMethods();
        this.updateOrderSummary();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Address form submission
        const addressForm = document.getElementById('address-form');
        if (addressForm) {
            addressForm.addEventListener('submit', (e) => this.handleAddressFormSubmit(e));
        }
    }

    async loadCartData() {
        try {
            const response = await fetch('/api/cart/api/detail/');
            if (response.ok) {
                this.cartData = await response.json();
                this.renderCartItems();
            }
        } catch (error) {
            console.error('Failed to load cart data:', error);
            showToast('Failed to load cart data', 'error');
        }
    }

    renderCartItems() {
        const container = document.getElementById('checkout-items');
        if (!container || !this.cartData) return;

        const items = this.cartData.items || [];
        
        if (items.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-shopping-cart text-4xl text-gray-300 mb-4"></i>
                    <p class="text-gray-600">Your cart is empty</p>
                    <a href="/products/" class="text-blue-600 hover:underline mt-2 inline-block">
                        Continue Shopping
                    </a>
                </div>
            `;
            return;
        }

        container.innerHTML = items.map(item => `
            <div class="flex items-center justify-between py-4 border-b">
                <div class="flex items-center space-x-4">
                    <div class="w-16 h-16 bg-gray-200 rounded flex items-center justify-center">
                        <i class="fas fa-image text-gray-400"></i>
                    </div>
                    <div>
                        <h3 class="font-semibold">${item.product?.name || 'Product'}</h3>
                        ${item.variant ? `<p class="text-sm text-gray-600">${item.variant.name}</p>` : ''}
                        <p class="text-sm text-gray-600">Quantity: ${item.quantity}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="font-semibold">$${(item.price * item.quantity).toFixed(2)}</p>
                    <p class="text-sm text-gray-600">$${item.price} each</p>
                </div>
            </div>
        `).join('');
    }

    async loadAddresses() {
        try {
            const response = await fetch('/api/users/api/profile/');
            if (response.ok) {
                const userData = await response.json();
                this.userAddresses = userData.addresses || [];
                this.renderAddresses(this.userAddresses);
            } else {
                console.error('Failed to load addresses:', response.status);
                this.showAddressFormFallback();
            }
        } catch (error) {
            console.error('Failed to load addresses:', error);
            this.showAddressFormFallback();
        }
    }

    showAddressFormFallback() {
        const shippingContainer = document.getElementById('shipping-addresses');
        const billingContainer = document.getElementById('billing-addresses');
        
        shippingContainer.innerHTML = `
            <div class="text-center py-4 border-2 border-dashed border-gray-300 rounded-lg">
                <i class="fas fa-map-marker-alt text-3xl text-gray-400 mb-2"></i>
                <p class="text-gray-500 mb-2">No shipping addresses found</p>
                <p class="text-sm text-gray-400">Please add a shipping address to continue</p>
            </div>
        `;
        
        billingContainer.innerHTML = `
            <div class="text-center py-4 border-2 border-dashed border-gray-300 rounded-lg">
                <i class="fas fa-receipt text-3xl text-gray-400 mb-2"></i>
                <p class="text-gray-500 mb-2">No billing addresses found</p>
                <p class="text-sm text-gray-400">Please add a billing address to continue</p>
            </div>
        `;
    }

    renderAddresses(addresses) {
        const shippingContainer = document.getElementById('shipping-addresses');
        const billingContainer = document.getElementById('billing-addresses');

        const shippingAddresses = addresses.filter(addr => addr.address_type === 'shipping');
        const billingAddresses = addresses.filter(addr => addr.address_type === 'billing');

        this.renderAddressList(shippingAddresses, shippingContainer, 'shipping');
        this.renderAddressList(billingAddresses, billingContainer, 'billing');

        // Set default addresses if available
        const defaultShipping = shippingAddresses.find(addr => addr.is_default);
        const defaultBilling = billingAddresses.find(addr => addr.is_default);
        
        if (defaultShipping) this.selectAddress(defaultShipping.id, 'shipping');
        if (defaultBilling) this.selectAddress(defaultBilling.id, 'billing');
    }

    renderAddressList(addresses, container, type) {
        if (addresses.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4 border-2 border-dashed border-gray-300 rounded-lg">
                    <i class="fas fa-${type === 'shipping' ? 'map-marker-alt' : 'receipt'} text-3xl text-gray-400 mb-2"></i>
                    <p class="text-gray-500 mb-2">No ${type} addresses found</p>
                    <p class="text-sm text-gray-400">Please add a ${type} address to continue</p>
                </div>
            `;
            return;
        }

        container.innerHTML = addresses.map(address => `
            <div class="border rounded-lg p-4 mb-3 cursor-pointer address-option ${address.is_default ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}" 
                 onclick="checkoutManager.selectAddress(${address.id}, '${type}')"
                 data-address-id="${address.id}">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="font-semibold">${address.street}</p>
                        <p class="text-sm text-gray-600">${address.city}, ${address.state} ${address.zip_code}</p>
                        <p class="text-sm text-gray-600">${address.country}</p>
                    </div>
                    ${address.is_default ? '<span class="bg-blue-500 text-white px-2 py-1 rounded text-xs">Default</span>' : ''}
                </div>
            </div>
        `).join('');
    }

    selectAddress(addressId, type) {
        // Update UI
        document.querySelectorAll(`.address-option`).forEach(option => {
            option.classList.remove('border-blue-500', 'bg-blue-50');
        });
        
        const selectedOption = document.querySelector(`[data-address-id="${addressId}"]`);
        if (selectedOption) {
            selectedOption.classList.add('border-blue-500', 'bg-blue-50');
        }

        // Store selection
        if (type === 'shipping') {
            this.shippingAddressId = addressId;
        } else {
            this.billingAddressId = addressId;
        }

        this.updatePlaceOrderButton();
    }

    async loadPaymentMethods() {
        const container = document.getElementById('payment-methods');
        container.innerHTML = `
            <div class="border rounded-lg p-4 cursor-pointer payment-option" onclick="checkoutManager.selectPaymentMethod('stripe')">
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        <i class="fab fa-cc-stripe text-2xl text-blue-600 mr-3"></i>
                        <div>
                            <p class="font-semibold">Credit/Debit Card</p>
                            <p class="text-sm text-gray-600">Pay with Visa, Mastercard, or American Express</p>
                        </div>
                    </div>
                    <i class="fas fa-check text-green-500 hidden"></i>
                </div>
            </div>
            
            <div class="border rounded-lg p-4 cursor-pointer payment-option" onclick="checkoutManager.selectPaymentMethod('cbe')">
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        <i class="fas fa-university text-2xl text-green-600 mr-3"></i>
                        <div>
                            <p class="font-semibold">CBE Birr</p>
                            <p class="text-sm text-gray-600">Pay with Commercial Bank of Ethiopia</p>
                        </div>
                    </div>
                    <i class="fas fa-check text-green-500 hidden"></i>
                </div>
            </div>
            
            <div class="border rounded-lg p-4 cursor-pointer payment-option" onclick="checkoutManager.selectPaymentMethod('telebirr')">
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        <i class="fas fa-mobile-alt text-2xl text-purple-600 mr-3"></i>
                        <div>
                            <p class="font-semibold">TeleBirr</p>
                            <p class="text-sm text-gray-600">Pay with Ethio Telecom mobile money</p>
                        </div>
                    </div>
                    <i class="fas fa-check text-green-500 hidden"></i>
                </div>
            </div>
        `;
    }

    selectPaymentMethod(method) {
        // Update UI
        document.querySelectorAll('.payment-option').forEach(option => {
            option.querySelector('.fa-check').classList.add('hidden');
        });
        
        const selectedOption = event.currentTarget;
        selectedOption.querySelector('.fa-check').classList.remove('hidden');

        // Store selection
        this.paymentMethod = method;
        this.updatePlaceOrderButton();
    }

    updateOrderSummary() {
        if (!this.cartData) return;

        const subtotal = this.cartData.subtotal || 0;
        const shippingCost = 5.00; // Fixed shipping for now
        const taxAmount = subtotal * 0.15; // 15% tax

        document.getElementById('subtotal').textContent = `$${subtotal.toFixed(2)}`;
        document.getElementById('shipping-cost').textContent = `$${shippingCost.toFixed(2)}`;
        document.getElementById('tax-amount').textContent = `$${taxAmount.toFixed(2)}`;
        document.getElementById('grand-total').textContent = `$${(subtotal + shippingCost + taxAmount).toFixed(2)}`;
    }

    updatePlaceOrderButton() {
        const button = document.getElementById('place-order-btn');
        const canPlaceOrder = this.shippingAddressId && this.billingAddressId && this.paymentMethod;
        
        button.disabled = !canPlaceOrder;
    }

    // Address creation methods
    async createAddress(addressData) {
    try {
        console.log('Creating address:', addressData);
        
        const response = await fetch('/api/users/api/addresses/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(addressData)
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Address created successfully:', result);
            showToast('Address created successfully', 'success');
            return result;
        } else {
            const errorData = await response.json();
            console.error('Address creation failed:', errorData);
            throw new Error(errorData.detail || 'Failed to create address');
        }
    } catch (error) {
        console.error('Address creation error:', error);
        showToast('Failed to create address: ' + error.message, 'error');
        throw error;
    }
}

    async createAddress(addressData) {
    try {
        console.log('Creating address:', addressData);
        
        const response = await fetch('/api/users/api/addresses/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(addressData)
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Address created successfully:', result);
            showToast('Address created successfully', 'success');
            return result;
        } else {
            const errorData = await response.json();
            console.error('Address creation failed:', errorData);
            throw new Error(errorData.detail || 'Failed to create address');
        }
    } catch (error) {
        console.error('Address creation error:', error);
        showToast('Failed to create address: ' + error.message, 'error');
        throw error;
    }
}

    
async handleAddressFormSubmit(event) {
    event.preventDefault();
    
    const addressType = document.getElementById('address-type').value;
    const street = document.getElementById('street').value;
    const city = document.getElementById('city').value;
    const state = document.getElementById('state').value;
    const zipCode = document.getElementById('zip-code').value;
    const country = document.getElementById('country').value;
    const isDefault = document.getElementById('is-default').checked;

    if (!street || !city || !state || !zipCode) {
        showToast('Please fill all required address fields', 'error');
        return;
    }

    const addressData = {
        address_type: addressType,
        street: street,
        city: city,
        state: state,
        zip_code: zipCode,
        country: country,
        is_default: isDefault
    };

    try {
        const newAddress = await this.createAddress(addressData);
        hideAddressForm();
        
        // Reload addresses and select the new one
        await this.loadAddresses();
        this.selectAddress(newAddress.id, addressType);
        
    } catch (error) {
        console.error('Failed to create address:', error);
    }
}

    toggleSameAsShipping() {
        const sameAsShipping = document.getElementById('same-as-shipping').checked;
        const billingSection = document.getElementById('billing-addresses').parentElement;
        
        if (sameAsShipping && this.shippingAddressId) {
            // Use shipping address for billing
            this.billingAddressId = this.shippingAddressId;
            
            // Update UI to show it's using shipping address
            billingSection.innerHTML = `
                <h2 class="text-xl font-semibold mb-4">Billing Address</h2>
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                    <div class="flex items-center text-green-700">
                        <i class="fas fa-check-circle mr-2"></i>
                        <span class="font-semibold">Using shipping address</span>
                    </div>
                    <p class="text-green-600 text-sm mt-1">Your billing address will be the same as your shipping address.</p>
                </div>
                <button onclick="showAddressForm('billing')" 
                        class="w-full bg-gray-600 text-white px-4 py-3 rounded-lg hover:bg-gray-700 transition-colors font-semibold">
                    <i class="fas fa-edit mr-2"></i>Use Different Billing Address
                </button>
            `;
            
            this.updatePlaceOrderButton();
        } else if (!sameAsShipping) {
            // Reload billing addresses
            this.loadAddresses();
        }
    }

    async placeOrder() {
        if (!this.shippingAddressId || !this.billingAddressId || !this.paymentMethod) {
            showToast('Please complete all required fields', 'error');
            return;
        }

        const button = document.getElementById('place-order-btn');
        const originalText = button.innerHTML;
        
        // Use ajaxUtils for loading state if available
        if (window.ajaxUtils) {
            window.ajaxUtils.showLoading(button, 'Placing Order...');
        } else {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Placing Order...';
        }

        try {
            const orderData = {
                shipping_address_id: this.shippingAddressId,
                billing_address_id: this.billingAddressId,
                payment_method: this.paymentMethod
            };

            console.log('Sending order data:', orderData);

            // Use ajaxUtils if available, otherwise use fetch
            let response;
            if (window.ajaxUtils) {
                response = await window.ajaxUtils.makeRequest(
                    '/api/orders/create/',
                    'POST',
                    orderData
                );
            } else {
                // Fallback to fetch
                const fetchResponse = await fetch('/api/orders/create/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify(orderData)
                });
                
                const data = await fetchResponse.json();
                response = {
                    success: fetchResponse.ok,
                    data: data,
                    status: fetchResponse.status
                };
            }

            console.log('Order response:', response);

            if (response.success) {
                showToast('Order placed successfully!', 'success');
                
                // Redirect to order detail page
                setTimeout(() => {
                    if (response.data && response.data.order) {
                        window.location.href = `/orders/${response.data.order.id}/`;
                    } else {
                        window.location.href = '/orders/';
                    }
                }, 2000);
            } else {
                console.error('Order creation failed:', response);
                
                // Handle different error types
                let errorMessage = 'Failed to place order';
                if (response.error) {
                    if (typeof response.error === 'string') {
                        errorMessage = response.error;
                    } else if (response.error.detail) {
                        errorMessage = response.error.detail;
                    } else if (response.error.error) {
                        errorMessage = response.error.error;
                    } else if (Array.isArray(response.error)) {
                        errorMessage = response.error.join(', ');
                    }
                }
                
                showToast(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Order placement error:', error);
            showToast('Network error. Please try again.', 'error');
        } finally {
            // Reset button state
            if (window.ajaxUtils) {
                window.ajaxUtils.hideLoading(button);
            } else {
                button.disabled = false;
                button.innerHTML = originalText;
            }
        }
    }
}

// Global functions for HTML onclick handlers
function showAddressForm(type) {
    document.getElementById('address-type').value = type;
    document.getElementById('modal-title').textContent = `Add ${type.charAt(0).toUpperCase() + type.slice(1)} Address`;
    document.getElementById('address-modal').classList.remove('hidden');
}

function hideAddressForm() {
    document.getElementById('address-modal').classList.add('hidden');
    document.getElementById('address-form').reset();
}

function toggleSameAsShipping() {
    if (checkoutManager) {
        checkoutManager.toggleSameAsShipping();
    }
}

function placeOrder() {
    if (checkoutManager) {
        checkoutManager.placeOrder();
    }
}

// Initialize checkout manager when DOM is loaded
let checkoutManager;
document.addEventListener('DOMContentLoaded', function() {
    checkoutManager = new CheckoutManager();
});

// Quick address creation for testing
async function createTestAddresses() {
    console.log("Creating test addresses...");
    
    const shippingAddress = {
        address_type: 'shipping',
        street: '123 Test Street',
        city: 'Addis Ababa',
        state: 'Addis Ababa',
        zip_code: '1000',
        country: 'Ethiopia',
        is_default: true
    };
    
    const billingAddress = {
        address_type: 'billing', 
        street: '123 Test Street',
        city: 'Addis Ababa',
        state: 'Addis Ababa',
        zip_code: '1000',
        country: 'Ethiopia',
        is_default: true
    };
    
    try {
        // Use the checkout manager to create addresses
        if (checkoutManager) {
            const shipping = await checkoutManager.createAddress(shippingAddress);
            const billing = await checkoutManager.createAddress(billingAddress);
            
            console.log('✅ Addresses created successfully!');
            console.log('Shipping:', shipping);
            console.log('Billing:', billing);
            
            // Reload addresses
            await checkoutManager.loadAddresses();
        } else {
            console.log('❌ Checkout manager not initialized');
        }
    } catch (error) {
        console.log('❌ Error creating addresses:', error);
    }
}