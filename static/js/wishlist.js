class WishlistManager {
    constructor() {
        this.initEventListeners();
        this.loadWishlistCount();
    }

    initEventListeners() {
        // Add to wishlist buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.add-to-wishlist-btn') || e.target.closest('.wishlist-toggle-btn')) {
                this.toggleWishlistItem(e.target.closest('button'));
            }
        });

        // Remove from wishlist
        document.addEventListener('click', (e) => {
            if (e.target.closest('.remove-from-wishlist-btn')) {
                this.removeFromWishlist(e.target.closest('button'));
            }
        });

        // Move to cart
        document.addEventListener('click', (e) => {
            if (e.target.closest('.move-to-cart-btn')) {
                this.moveToCart(e.target.closest('button'));
            }
        });

        // Bulk actions
        document.addEventListener('click', (e) => {
            if (e.target.id === 'move-selected-to-cart') {
                this.moveSelectedToCart();
            }
            if (e.target.id === 'remove-selected-from-wishlist') {
                this.removeSelectedFromWishlist();
            }
        });
    }

    async toggleWishlistItem(button) {
        const productId = button.dataset.productId;
        const isInWishlist = button.classList.contains('in-wishlist');

        ajaxUtils.showLoading(button, isInWishlist ? 'Removing...' : 'Adding...');

        const url = isInWishlist ? 
            `/api/wishlist/remove/${productId}/` : 
            `/api/wishlist/add/${productId}/`;

        const method = isInWishlist ? 'DELETE' : 'POST';

        const response = await ajaxUtils.makeRequest(url, method);

        if (response.success) {
            if (isInWishlist) {
                ajaxUtils.showMessage('Removed from wishlist');
                this.updateWishlistButton(button, false);
            } else {
                ajaxUtils.showMessage('Added to wishlist!');
                this.updateWishlistButton(button, true);
            }
            
            this.loadWishlistCount();
        } else {
            ajaxUtils.showMessage('Operation failed', 'error');
        }

        ajaxUtils.hideLoading(button);
    }

    updateWishlistButton(button, isInWishlist) {
        const icon = button.querySelector('i');
        
        if (isInWishlist) {
            button.classList.add('in-wishlist');
            icon.classList.remove('far', 'fa-heart');
            icon.classList.add('fas', 'fa-heart', 'text-red-500');
        } else {
            button.classList.remove('in-wishlist');
            icon.classList.remove('fas', 'fa-heart', 'text-red-500');
            icon.classList.add('far', 'fa-heart');
        }
    }

    async removeFromWishlist(button) {
        const productId = button.dataset.productId;

        if (!confirm('Are you sure you want to remove this item from your wishlist?')) {
            return;
        }

        const response = await ajaxUtils.makeRequest(`/api/wishlist/remove/${productId}/`, 'DELETE');

        if (response.success) {
            ajaxUtils.showMessage('Item removed from wishlist');
            this.loadWishlistCount();
            
            // Remove from DOM
            const itemElement = button.closest('.wishlist-item');
            if (itemElement) {
                itemElement.remove();
                this.updateWishlistEmptyState();
            }
        } else {
            ajaxUtils.showMessage('Failed to remove item', 'error');
        }
    }

    async moveToCart(button) {
        const productId = button.dataset.productId;

        ajaxUtils.showLoading(button, 'Moving...');

        const response = await ajaxUtils.makeRequest('/api/wishlist/move-to-cart/', 'POST', {
            item_ids: [productId]
        });

        if (response.success) {
            ajaxUtils.showMessage('Item moved to cart!');
            
            // Update cart count
            if (typeof cartManager !== 'undefined') {
                cartManager.loadCartCount();
            }
            
            // Remove from wishlist
            const itemElement = button.closest('.wishlist-item');
            if (itemElement) {
                itemElement.remove();
                this.updateWishlistEmptyState();
            }
            
            this.loadWishlistCount();
        } else {
            ajaxUtils.showMessage('Failed to move item to cart', 'error');
        }

        ajaxUtils.hideLoading(button);
    }

    async moveSelectedToCart() {
        const selectedItems = this.getSelectedItems();
        
        if (selectedItems.length === 0) {
            ajaxUtils.showMessage('Please select items to move to cart', 'warning');
            return;
        }

        const response = await ajaxUtils.makeRequest('/api/wishlist/move-to-cart/', 'POST', {
            item_ids: selectedItems
        });

        if (response.success) {
            ajaxUtils.showMessage(`Moved ${response.data.moved_items.length} items to cart`);
            
            // Update counts
            if (typeof cartManager !== 'undefined') {
                cartManager.loadCartCount();
            }
            
            // Remove moved items from DOM
            selectedItems.forEach(itemId => {
                const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
                if (itemElement) {
                    itemElement.closest('.wishlist-item').remove();
                }
            });
            
            this.updateWishlistEmptyState();
            this.loadWishlistCount();
        } else {
            ajaxUtils.showMessage('Failed to move items to cart', 'error');
        }
    }

    async removeSelectedFromWishlist() {
        const selectedItems = this.getSelectedItems();
        
        if (selectedItems.length === 0) {
            ajaxUtils.showMessage('Please select items to remove', 'warning');
            return;
        }

        if (!confirm(`Are you sure you want to remove ${selectedItems.length} items from your wishlist?`)) {
            return;
        }

        // Remove each item individually
        let removedCount = 0;
        for (const itemId of selectedItems) {
            const response = await ajaxUtils.makeRequest(`/api/wishlist/remove/${itemId}/`, 'DELETE');
            if (response.success) {
                removedCount++;
                
                // Remove from DOM
                const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
                if (itemElement) {
                    itemElement.closest('.wishlist-item').remove();
                }
            }
        }

        if (removedCount > 0) {
            ajaxUtils.showMessage(`Removed ${removedCount} items from wishlist`);
            this.updateWishlistEmptyState();
            this.loadWishlistCount();
        }
    }

    getSelectedItems() {
        const checkboxes = document.querySelectorAll('.wishlist-item-checkbox:checked');
        return Array.from(checkboxes).map(checkbox => checkbox.value);
    }

    updateWishlistEmptyState() {
        const container = document.getElementById('wishlist-items-container');
        const emptyState = document.getElementById('wishlist-empty-state');
        
        if (container && emptyState) {
            const hasItems = container.querySelector('.wishlist-item');
            if (!hasItems) {
                emptyState.classList.remove('hidden');
            } else {
                emptyState.classList.add('hidden');
            }
        }
    }

    async loadWishlistCount() {
        const response = await ajaxUtils.makeRequest('/api/wishlist/');
        
        if (response.success) {
            const count = response.data.item_count || 0;
            ajaxUtils.updateCounter('wishlist-count', count);
        }
    }

    async checkWishlistStatus(productId) {
        const response = await ajaxUtils.makeRequest(`/api/wishlist/check/${productId}/`);
        
        if (response.success) {
            const buttons = document.querySelectorAll(`[data-product-id="${productId}"]`);
            buttons.forEach(button => {
                this.updateWishlistButton(button, response.data.is_in_wishlist);
            });
        }
    }

    // Share wishlist functionality
    async shareWishlist() {
        const response = await ajaxUtils.makeRequest('/api/wishlist/share/', 'POST', {
            message: 'Check out my wishlist!'
        });

        if (response.success) {
            const shareUrl = response.data.share_url;
            
            // Copy to clipboard
            try {
                await navigator.clipboard.writeText(shareUrl);
                ajaxUtils.showMessage('Wishlist share link copied to clipboard!');
            } catch (err) {
                // Fallback: show share URL
                prompt('Share this link:', shareUrl);
            }
        } else {
            ajaxUtils.showMessage('Failed to share wishlist', 'error');
        }
    }
}

// Initialize wishlist manager
document.addEventListener('DOMContentLoaded', function() {
    new WishlistManager();
});