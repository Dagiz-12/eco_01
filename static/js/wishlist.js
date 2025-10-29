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
    }

    async toggleWishlistItem(button) {
        const productId = button.dataset.productId;
        const isInWishlist = button.classList.contains('in-wishlist');

        if (window.ajaxUtils) {
            window.ajaxUtils.showLoading(button, isInWishlist ? 'Removing...' : 'Adding...');
        }

        try {
            const url = isInWishlist ? 
                `/api/wishlist/remove/${productId}/` : 
                `/api/wishlist/add/${productId}/`;

            const method = isInWishlist ? 'DELETE' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                const message = isInWishlist ? 'Removed from wishlist' : 'Added to wishlist!';
                
                if (window.showToast) {
                    window.showToast(message, 'success');
                }
                this.updateWishlistButton(button, !isInWishlist);
                this.loadWishlistCount();
            } else {
                const errorData = await response.json();
                if (window.showToast) {
                    window.showToast(errorData.message || 'Operation failed', 'error');
                }
            }
        } catch (error) {
            console.error('Wishlist toggle error:', error);
            if (window.showToast) {
                window.showToast('Network error. Please try again.', 'error');
            }
        } finally {
            if (window.ajaxUtils) {
                window.ajaxUtils.hideLoading(button);
            }
        }
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

        try {
            const response = await fetch(`/api/wishlist/remove/${productId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                if (window.showToast) {
                    window.showToast('Item removed from wishlist', 'success');
                }
                this.loadWishlistCount();
                
                // Remove from DOM
                const itemElement = button.closest('.wishlist-item');
                if (itemElement) {
                    itemElement.remove();
                    this.updateWishlistEmptyState();
                }
            } else {
                if (window.showToast) {
                    window.showToast('Failed to remove item', 'error');
                }
            }
        } catch (error) {
            console.error('Remove from wishlist error:', error);
        }
    }

    async loadWishlistCount() {
        try {
            const response = await fetch('/api/wishlist/');
            if (response.ok) {
                const data = await response.json();
                const count = data.item_count || 0;
                const counter = document.getElementById('wishlist-count');
                if (counter) {
                    counter.textContent = count;
                    if (count > 0) {
                        counter.classList.remove('hidden');
                    }
                }
            }
        } catch (error) {
            console.error('Failed to load wishlist count:', error);
        }
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
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
}

// Initialize wishlist manager
document.addEventListener('DOMContentLoaded', function() {
    window.wishlistManager = new WishlistManager();
});