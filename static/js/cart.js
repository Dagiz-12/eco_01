class CartManager {
    constructor() {
        this.initEventListeners();
        this.loadCartCount();
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
        const quantity = 1;

        if (window.ajaxUtils) {
            window.ajaxUtils.showLoading(button, 'Adding...');
        }

        try {
            // ✅ CORRECT URL: /api/cart/items/add/ (not /api/cart/add/)
            const response = await fetch('/api/cart/items/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    product_id: parseInt(productId),
                    quantity: quantity
                })
            });

            // Check if response is OK
            if (response.ok) {
                const data = await response.json();
                
                if (window.showToast) {
                    window.showToast('Product added to cart!', 'success');
                }
                this.loadCartCount();
                
                // Update button state
                this.updateCartButtonState(button, true);
            } else {
                // Handle non-OK responses
                const errorData = await response.json();
                if (window.showToast) {
                    window.showToast(errorData.message || 'Failed to add product to cart', 'error');
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
            // ✅ CORRECT URL: /api/cart/items/{item_id}/update/
            const response = await fetch(`/api/cart/items/${itemId}/update/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
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
            // ✅ CORRECT URL: /api/cart/items/{item_id}/remove/
            const response = await fetch(`/api/cart/items/${itemId}/remove/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
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
                    const cartResponse = await fetch('/api/cart/');
                    if (cartResponse.ok) {
                        const cartData = await cartResponse.json();
                        this.updateCartTotals(cartData);
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
            const response = await fetch('/api/cart/');
            if (response.ok) {
                const data = await response.json();
                const count = data.total_items || 0;
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
                element.textContent = `$${parseFloat(value).toFixed(2)}`;
            }
        }
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
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
}

// Initialize cart manager
document.addEventListener('DOMContentLoaded', function() {
    window.cartManager = new CartManager();
});