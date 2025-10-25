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
        const variantId = button.dataset.variantId;
        const quantity = button.dataset.quantity || 1;

        ajaxUtils.showLoading(button, 'Adding...');

        const response = await ajaxUtils.makeRequest('/api/cart/add/', 'POST', {
            product_id: productId,
            variant_id: variantId,
            quantity: parseInt(quantity)
        });

        if (response.success) {
            ajaxUtils.showMessage('Product added to cart!');
            this.loadCartCount();
            
            // Update cart sidebar if open
            this.updateCartSidebar(response.data);
        } else {
            ajaxUtils.showMessage('Failed to add product to cart', 'error');
        }

        ajaxUtils.hideLoading(button);
    }

    async updateCartItem(input) {
        const itemId = input.dataset.itemId;
        const quantity = parseInt(input.value);

        if (quantity < 1) {
            this.removeFromCart(input);
            return;
        }

        const response = await ajaxUtils.makeRequest(`/api/cart/items/${itemId}/`, 'PATCH', {
            quantity: quantity
        });

        if (response.success) {
            this.updateCartTotals(response.data);
            ajaxUtils.showMessage('Cart updated!');
        } else {
            ajaxUtils.showMessage('Failed to update cart', 'error');
            // Revert input value
            input.value = input.dataset.originalValue;
        }
    }

    async removeFromCart(button) {
        const itemId = button.dataset.itemId;

        if (!confirm('Are you sure you want to remove this item from your cart?')) {
            return;
        }

        const response = await ajaxUtils.makeRequest(`/api/cart/items/${itemId}/`, 'DELETE');

        if (response.success) {
            ajaxUtils.showMessage('Item removed from cart');
            this.loadCartCount();
            
            // Remove item from DOM
            const itemElement = button.closest('.cart-item');
            if (itemElement) {
                itemElement.remove();
                this.updateCartTotals(response.data);
            }
        } else {
            ajaxUtils.showMessage('Failed to remove item', 'error');
        }
    }

    async loadCartCount() {
        const response = await ajaxUtils.makeRequest('/api/cart/');
        
        if (response.success) {
            const count = response.data.total_items || 0;
            ajaxUtils.updateCounter('cart-count', count);
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

    updateCartSidebar(cartData) {
        const sidebar = document.getElementById('cart-sidebar');
        if (sidebar && sidebar.classList.contains('active')) {
            // Refresh cart sidebar content
            this.refreshCartSidebar();
        }
    }

    async refreshCartSidebar() {
        const response = await ajaxUtils.makeRequest('/api/cart/');
        
        if (response.success) {
            const sidebar = document.getElementById('cart-sidebar-content');
            if (sidebar) {
                // This would typically render a template
                sidebar.innerHTML = this.renderCartItems(response.data.items);
            }
        }
    }

    renderCartItems(items) {
        if (!items || items.length === 0) {
            return '<p class="text-gray-500">Your cart is empty</p>';
        }

        return items.map(item => `
            <div class="cart-sidebar-item flex items-center space-x-3 py-3 border-b">
                <img src="${item.product.image}" alt="${item.product.name}" 
                     class="w-16 h-16 object-cover rounded">
                <div class="flex-1">
                    <h4 class="font-semibold text-sm">${item.product.name}</h4>
                    <p class="text-gray-600 text-sm">$${item.price} x ${item.quantity}</p>
                </div>
                <button class="remove-from-cart-btn text-red-500" 
                        data-item-id="${item.id}">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }
}

// Initialize cart manager
document.addEventListener('DOMContentLoaded', function() {
    new CartManager();
});