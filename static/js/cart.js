class CartManager {
    constructor() {
        this.initEventListeners();
        this.loadCartCount();
        this.loadCartPage(); // Load cart page if we're on cart page
    }

    initEventListeners() {
        // Add to cart buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.add-to-cart-btn')) {
                this.addToCart(e.target.closest('.add-to-cart-btn'));
            }
        });

        // Cart quantity updates
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('cart-quantity')) {
                this.updateCartItem(e.target);
            }
        });

        // Remove from cart
        document.addEventListener('click', (e) => {
            if (e.target.closest('.remove-from-cart-btn')) {
                this.removeFromCart(e.target.closest('.remove-from-cart-btn'));
            }
        });
    }

    async addToCart(button) {
        const productId = button.dataset.productId;
        console.log('Add to cart clicked', productId);

        if (window.ajaxUtils) {
            window.ajaxUtils.showLoading(button, 'Adding...');
        }

        try {
            const csrfToken = this.getCSRFToken();
            
            const response = await fetch('/api/cart/api/items/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    product_id: parseInt(productId),
                    quantity: 1
                })
            });

            console.log('Response status:', response.status);
            
            // Handle non-JSON responses
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Non-JSON response:', text.substring(0, 200));
                throw new Error('Server returned non-JSON response');
            }

            const data = await response.json();
            
            if (response.ok) {
                if (window.showToast) {
                    window.showToast('Product added to cart!', 'success');
                }
                this.loadCartCount();
                this.updateCartButtonState(button, true);
            } else {
                if (window.showToast) {
                    window.showToast(data.message || 'Failed to add product to cart', 'error');
                }
            }
        } catch (error) {
            console.error('Add to cart error:', error);
            if (window.showToast) {
                window.showToast('Network error. Please try again.', 'error');
            }
        } finally {
            if (window.ajaxUtils) {
                window.ajaxUtils.hideLoading(button);
            }
        }
    }

    async updateCartItem(input) {
        const itemId = input.dataset.itemId;
        const quantity = parseInt(input.value);

        if (quantity < 1) {
            this.removeFromCart(input);
            return;
        }

        try {
            const response = await fetch(`/api/cart/api/items/${itemId}/update/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ quantity: quantity })
            });

            if (response.ok) {
                const data = await response.json();
                this.updateCartTotals(data);
                if (window.showToast) {
                    window.showToast('Cart updated!', 'success');
                }
            } else {
                if (window.showToast) {
                    window.showToast('Failed to update cart', 'error');
                }
                // Revert input value
                input.value = input.dataset.originalValue;
            }
        } catch (error) {
            console.error('Update cart item error:', error);
        }
    }

    async removeFromCart(button) {
        const itemId = button.dataset.itemId;

        if (!confirm('Are you sure you want to remove this item from your cart?')) {
            return;
        }

        try {
            const response = await fetch(`/api/cart/api/items/${itemId}/remove/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                if (window.showToast) {
                    window.showToast('Item removed from cart', 'success');
                }
                this.loadCartCount();
                
                // Remove item from DOM
                const itemElement = button.closest('.cart-item');
                if (itemElement) {
                    itemElement.remove();
                    // Update totals if needed
                    const cartResponse = await fetch('/api/cart/api/detail/');
                    if (cartResponse.ok) {
                        const cartData = await cartResponse.json();
                        this.updateCartTotals(cartData);
                        this.checkEmptyCart();
                    }
                }
            } else {
                if (window.showToast) {
                    window.showToast('Failed to remove item', 'error');
                }
            }
        } catch (error) {
            console.error('Remove from cart error:', error);
        }
    }

    async loadCartCount() {
        try {
            const response = await fetch('/api/cart/api/detail/');
            
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Cart count: Non-JSON response received');
                return;
            }
            
            if (response.ok) {
                const data = await response.json();
                const count = data.total_items || data.items?.length || 0;
                const counter = document.getElementById('cart-count');
                if (counter) {
                    counter.textContent = count;
                    counter.classList.remove('hidden');
                }
            }
        } catch (error) {
            console.error('Failed to load cart count:', error);
        }
    }

    async loadCartPage() {
        // Only run on cart page
        if (!document.getElementById('cart-items-container')) {
            return;
        }

        try {
            const response = await fetch('/api/cart/api/detail/');
            if (response.ok) {
                const cartData = await response.json();
                this.renderCartPage(cartData);
            } else {
                console.error('Failed to load cart page data');
                this.showEmptyCart();
            }
        } catch (error) {
            console.error('Error loading cart page:', error);
            this.showEmptyCart();
        }
    }

    renderCartPage(cartData) {
        const container = document.getElementById('cart-items-container');
        const emptyCart = document.getElementById('empty-cart');
        const checkoutBtn = document.getElementById('checkout-btn');
        
        if (!container) return;

        // Check if cart is empty
        if (!cartData.items || cartData.items.length === 0) {
            this.showEmptyCart();
            return;
        }

        // Hide empty state, show checkout button
        if (emptyCart) emptyCart.classList.add('hidden');
        if (checkoutBtn) checkoutBtn.classList.remove('hidden');

        // Render cart items
        container.innerHTML = cartData.items.map(item => `
            <div class="cart-item flex items-center space-x-4 py-4 border-b border-gray-200">
                <img src="${item.product?.image || item.product?.primary_image || '/static/images/placeholder.jpg'}" 
                     alt="${item.product?.name || 'Product'}" 
                     class="w-16 h-16 object-cover rounded">
                <div class="flex-1">
                    <h4 class="font-semibold text-gray-900">${item.product?.name || 'Unknown Product'}</h4>
                    <p class="text-gray-600">$${item.product?.price || '0.00'}</p>
                </div>
                <div class="flex items-center space-x-2">
                    <button class="quantity-btn decrease-qty px-2 py-1 border rounded hover:bg-gray-100" 
                            data-item-id="${item.id}">-</button>
                    <span class="quantity w-8 text-center">${item.quantity}</span>
                    <button class="quantity-btn increase-qty px-2 py-1 border rounded hover:bg-gray-100" 
                            data-item-id="${item.id}">+</button>
                </div>
                <div class="text-right">
                    <p class="font-semibold">$${((item.product?.price || 0) * item.quantity).toFixed(2)}</p>
                    <button class="remove-from-cart-btn text-red-500 hover:text-red-700 mt-1 text-sm" 
                            data-item-id="${item.id}">Remove</button>
                </div>
            </div>
        `).join('');

        // Update order summary
        this.updateOrderSummary(cartData);
        
        // Add event listeners for cart page buttons
        this.initCartPageEventListeners();
    }

    showEmptyCart() {
        const container = document.getElementById('cart-items-container');
        const emptyCart = document.getElementById('empty-cart');
        const checkoutBtn = document.getElementById('checkout-btn');
        
        if (container) container.innerHTML = '';
        if (emptyCart) emptyCart.classList.remove('hidden');
        if (checkoutBtn) checkoutBtn.classList.add('hidden');
        
        this.updateOrderSummary({
            subtotal: 0,
            shipping_cost: 0,
            tax_amount: 0,
            total: 0
        });
    }

    initCartPageEventListeners() {
        // Quantity buttons
        document.querySelectorAll('.quantity-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemId = e.target.dataset.itemId;
                const action = e.target.classList.contains('increase-qty') ? 'increase' : 'decrease';
                this.handleQuantityChange(itemId, action);
            });
        });

        // Remove buttons
        document.querySelectorAll('.remove-from-cart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemId = e.target.dataset.itemId;
                this.removeFromCart(e.target);
            });
        });
    }

    async handleQuantityChange(itemId, action) {
        try {
            // Get current quantity
            const quantityElement = document.querySelector(`[data-item-id="${itemId}"] + .quantity`);
            if (!quantityElement) return;
            
            let currentQuantity = parseInt(quantityElement.textContent);
            
            // Calculate new quantity
            let newQuantity = action === 'increase' ? currentQuantity + 1 : currentQuantity - 1;
            
            if (newQuantity < 1) {
                this.removeFromCart(document.querySelector(`.remove-from-cart-btn[data-item-id="${itemId}"]`));
                return;
            }

            // Update via API
            const response = await fetch(`/api/cart/api/items/${itemId}/update/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ quantity: newQuantity })
            });

            if (response.ok) {
                const data = await response.json();
                // Reload the entire cart page to get fresh data
                this.loadCartPage();
                this.loadCartCount();
                if (window.showToast) {
                    window.showToast('Cart updated!', 'success');
                }
            } else {
                throw new Error('Failed to update quantity');
            }
        } catch (error) {
            console.error('Quantity update error:', error);
            if (window.showToast) {
                window.showToast('Failed to update quantity', 'error');
            }
        }
    }

    checkEmptyCart() {
        const cartItems = document.querySelectorAll('.cart-item');
        if (cartItems.length === 0) {
            this.showEmptyCart();
        }
    }

    updateCartTotals(cartData) {
        // Update subtotal, tax, shipping, grand total
        const elements = {
            'subtotal': cartData.subtotal,
            'tax_amount': cartData.tax_amount,
            'shipping_cost': cartData.shipping_cost,
            'grand_total': cartData.grand_total
        };

        for (const [key, value] of Object.entries(elements)) {
            const element = document.getElementById(`cart-${key}`);
            if (element) {
                element.textContent = `$${parseFloat(value || 0).toFixed(2)}`;
            }
        }
    }

    updateOrderSummary(cartData) {
        const subtotal = document.getElementById('cart-subtotal');
        const shipping = document.getElementById('cart-shipping-cost');
        const tax = document.getElementById('cart-tax-amount');
        const total = document.getElementById('cart-grand-total');
        
        if (subtotal) subtotal.textContent = `$${(cartData.subtotal || 0).toFixed(2)}`;
        if (shipping) shipping.textContent = `$${(cartData.shipping_cost || 0).toFixed(2)}`;
        if (tax) tax.textContent = `$${(cartData.tax_amount || 0).toFixed(2)}`;
        if (total) total.textContent = `$${(cartData.total || 0).toFixed(2)}`;
    }

    updateCartButtonState(button, isInCart) {
        if (isInCart) {
            button.innerHTML = '<i class="fas fa-check mr-2"></i>In Cart';
            button.classList.remove('bg-blue-600', 'hover:bg-blue-700');
            button.classList.add('bg-green-600', 'hover:bg-green-700');
            button.disabled = true;
        } else {
            button.innerHTML = '<i class="fas fa-shopping-cart mr-2"></i>Add to Cart';
            button.classList.remove('bg-green-600', 'hover:bg-green-700');
            button.classList.add('bg-blue-600', 'hover:bg-blue-700');
            button.disabled = false;
        }
    }

    getCSRFToken() {
        // Get CSRF token from form input
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            return csrfToken.value;
        }
        
        // Alternative method to get CSRF token from cookies
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
}

// Initialize cart manager
document.addEventListener('DOMContentLoaded', function() {
    window.cartManager = new CartManager();
});