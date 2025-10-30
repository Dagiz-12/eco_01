class WishlistManager {
    constructor() {
        this.initEventListeners();
        this.loadWishlistCount();
        this.loadWishlistPage(); // Load wishlist page if we're on wishlist page
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
            if (e.target.closest('#move-all-to-cart')) {
                this.moveAllToCart();
            }
            if (e.target.closest('#share-wishlist-btn')) {
                this.shareWishlist();
            }
            if (e.target.closest('#move-selected-to-cart')) {
                this.moveSelectedToCart();
            }
            if (e.target.closest('#remove-selected-from-wishlist')) {
                this.removeSelectedFromWishlist();
            }
            if (e.target.closest('#clear-selection')) {
                this.clearSelection();
            }
        });

        // Checkbox selection
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('wishlist-item-checkbox')) {
                this.handleItemSelection(e.target);
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
                `/api/wishlist/api/remove/${productId}/` : 
                `/api/wishlist/api/add/${productId}/`;

            const method = isInWishlist ? 'DELETE' : 'POST';

            console.log(`Making ${method} request to: ${url}`);

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                // For POST requests, send product ID in body
                body: method === 'POST' ? JSON.stringify({ product: parseInt(productId) }) : undefined
            });

            console.log('Wishlist response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Wishlist error response:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            console.log('Wishlist response data:', data);
            
            const message = isInWishlist ? 'Removed from wishlist' : 'Added to wishlist!';
            
            if (window.showToast) {
                window.showToast(message, 'success');
            }
            
            this.updateWishlistButton(button, !isInWishlist);
            this.loadWishlistCount();
            
        } catch (error) {
            console.error('Wishlist toggle error:', error);
            if (window.showToast) {
                window.showToast('Failed to update wishlist. Please try again.', 'error');
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
            const response = await fetch(`/api/wishlist/api/remove/${productId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
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
                    this.updateWishlistStats();
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
            const response = await fetch('/api/wishlist/api/detail/');
            if (response.ok) {
                const data = await response.json();
                // Handle different response structures
                const count = data.item_count || data.items?.length || (data.items ? data.items.length : 0);
                const counter = document.getElementById('wishlist-count');
                if (counter) {
                    counter.textContent = count;
                    if (count > 0) {
                        counter.classList.remove('hidden');
                    } else {
                        counter.classList.add('hidden');
                    }
                }
            }
        } catch (error) {
            console.error('Failed to load wishlist count:', error);
        }
    }

    async loadWishlistPage() {
        // Only run on wishlist page
        if (!document.getElementById('wishlist-items-container')) {
            return;
        }

        try {
            const response = await fetch('/api/wishlist/api/detail/');
            if (response.ok) {
                const wishlistData = await response.json();
                console.log('Wishlist page data:', wishlistData); // Debug log
                this.renderWishlistPage(wishlistData);
            } else {
                console.error('Failed to load wishlist page data');
                this.showEmptyWishlist();
            }
        } catch (error) {
            console.error('Error loading wishlist page:', error);
            this.showEmptyWishlist();
        }
    }

    renderWishlistPage(wishlistData) {
        const container = document.getElementById('wishlist-items-container');
        const emptyState = document.getElementById('wishlist-empty-state');
        
        if (!container) return;

        // Check if wishlist is empty - handle different response structures
        const items = wishlistData.items || wishlistData.wishlist_items || [];
        
        if (!items || items.length === 0) {
            this.showEmptyWishlist();
            return;
        }

        // Hide empty state
        if (emptyState) emptyState.classList.add('hidden');

        // Render wishlist items
        container.innerHTML = items.map(item => {
            // Handle different item structures
            const product = item.product || item;
            const itemId = item.id || product.id;
            const productId = product.id;
            const productName = product.name || 'Unknown Product';
            const productPrice = product.price || 0;
            const productImage = product.image || product.primary_image || '/static/images/placeholder.jpg';
            const notes = item.notes || '';

            return `
            <div class="wishlist-item bg-white rounded-lg shadow-md p-4 mb-4">
                <div class="flex items-center space-x-4">
                    <!-- Checkbox for bulk actions -->
                    <input type="checkbox" class="wishlist-item-checkbox" data-item-id="${itemId}">
                    
                    <!-- Product Image -->
                    <img src="${productImage}" 
                         alt="${productName}" 
                         class="w-16 h-16 object-cover rounded">
                    
                    <!-- Product Details -->
                    <div class="flex-1">
                        <h4 class="font-semibold text-gray-900">${productName}</h4>
                        <p class="text-gray-600">$${parseFloat(productPrice).toFixed(2)}</p>
                        ${notes ? `<p class="text-sm text-gray-500 mt-1">${notes}</p>` : ''}
                    </div>
                    
                    <!-- Actions -->
                    <div class="flex flex-col space-y-2">
                        <button class="move-to-cart-btn bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                                data-item-id="${itemId}"
                                data-product-id="${productId}">
                            <i class="fas fa-shopping-cart mr-2"></i>Move to Cart
                        </button>
                        <button class="remove-from-wishlist-btn text-red-500 hover:text-red-700"
                                data-product-id="${productId}">
                            <i class="fas fa-trash mr-2"></i>Remove
                        </button>
                    </div>
                </div>
            </div>
            `;
        }).join('');

        // Update wishlist stats
        this.updateWishlistStats(items);
        
        // Add event listeners for wishlist page buttons
        this.initWishlistPageEventListeners();
    }

    showEmptyWishlist() {
        const container = document.getElementById('wishlist-items-container');
        const emptyState = document.getElementById('wishlist-empty-state');
        const bulkActions = document.getElementById('bulk-actions');
        
        if (container) container.innerHTML = '';
        if (emptyState) emptyState.classList.remove('hidden');
        if (bulkActions) bulkActions.classList.add('hidden');
        
        this.updateWishlistStats([]);
    }

    initWishlistPageEventListeners() {
        // Move to cart buttons
        document.querySelectorAll('.move-to-cart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemId = e.target.dataset.itemId;
                this.moveSingleToCart(itemId);
            });
        });

        // Remove buttons
        document.querySelectorAll('.remove-from-wishlist-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = e.target.dataset.productId;
                this.removeFromWishlist(e.target);
            });
        });
    }

    async moveSingleToCart(itemId) {
        try {
            const response = await fetch('/api/wishlist/api/move-to-cart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ item_ids: [parseInt(itemId)] })
            });

            if (response.ok) {
                const data = await response.json();
                if (window.showToast) {
                    window.showToast('Item moved to cart!', 'success');
                }
                
                // Remove from wishlist
                const itemElement = document.querySelector(`.wishlist-item-checkbox[data-item-id="${itemId}"]`)?.closest('.wishlist-item');
                if (itemElement) {
                    itemElement.remove();
                    this.updateWishlistEmptyState();
                    this.loadWishlistPage(); // Reload to get updated stats
                }
                
                this.loadWishlistCount();
                
                // Reload cart count
                if (window.cartManager) {
                    window.cartManager.loadCartCount();
                }
            } else {
                throw new Error('Failed to move item to cart');
            }
        } catch (error) {
            console.error('Move to cart error:', error);
            if (window.showToast) {
                window.showToast('Failed to move item to cart', 'error');
            }
        }
    }

    async moveAllToCart() {
        try {
            const response = await fetch('/api/wishlist/api/detail/');
            if (!response.ok) throw new Error('Failed to load wishlist');
            
            const wishlistData = await response.json();
            const items = wishlistData.items || wishlistData.wishlist_items || [];
            const itemIds = items.map(item => item.id || item.product?.id);
            
            if (itemIds.length === 0) {
                if (window.showToast) {
                    window.showToast('No items to move', 'info');
                }
                return;
            }

            const moveResponse = await fetch('/api/wishlist/api/move-to-cart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ item_ids: itemIds })
            });

            if (moveResponse.ok) {
                const data = await moveResponse.json();
                if (window.showToast) {
                    window.showToast(`Moved ${data.moved_items?.length || 0} items to cart!`, 'success');
                }
                
                // Clear wishlist
                this.showEmptyWishlist();
                this.loadWishlistCount();
                
                // Reload cart count
                if (window.cartManager) {
                    window.cartManager.loadCartCount();
                }
            } else {
                throw new Error('Failed to move items to cart');
            }
        } catch (error) {
            console.error('Move all to cart error:', error);
            if (window.showToast) {
                window.showToast('Failed to move items to cart', 'error');
            }
        }
    }

    handleItemSelection(checkbox) {
        const bulkActions = document.getElementById('bulk-actions');
        const selectedCount = document.getElementById('selected-count');
        
        if (!bulkActions || !selectedCount) return;
        
        const selectedItems = document.querySelectorAll('.wishlist-item-checkbox:checked');
        const count = selectedItems.length;
        
        selectedCount.textContent = `${count} items selected`;
        
        if (count > 0) {
            bulkActions.classList.remove('hidden');
        } else {
            bulkActions.classList.add('hidden');
        }
    }

    async moveSelectedToCart() {
        const selectedItems = document.querySelectorAll('.wishlist-item-checkbox:checked');
        const itemIds = Array.from(selectedItems).map(checkbox => parseInt(checkbox.dataset.itemId));
        
        if (itemIds.length === 0) {
            if (window.showToast) {
                window.showToast('No items selected', 'info');
            }
            return;
        }

        try {
            const response = await fetch('/api/wishlist/api/move-to-cart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ item_ids: itemIds })
            });

            if (response.ok) {
                const data = await response.json();
                if (window.showToast) {
                    window.showToast(`Moved ${data.moved_items?.length || 0} items to cart!`, 'success');
                }
                
                // Remove selected items from DOM
                selectedItems.forEach(checkbox => {
                    const itemElement = checkbox.closest('.wishlist-item');
                    if (itemElement) {
                        itemElement.remove();
                    }
                });
                
                this.updateWishlistEmptyState();
                this.loadWishlistPage(); // Reload to get updated stats
                this.loadWishlistCount();
                this.clearSelection();
                
                // Reload cart count
                if (window.cartManager) {
                    window.cartManager.loadCartCount();
                }
            } else {
                throw new Error('Failed to move selected items to cart');
            }
        } catch (error) {
            console.error('Move selected to cart error:', error);
            if (window.showToast) {
                window.showToast('Failed to move selected items to cart', 'error');
            }
        }
    }

    async removeSelectedFromWishlist() {
        const selectedItems = document.querySelectorAll('.wishlist-item-checkbox:checked');
        const productIds = Array.from(selectedItems).map(checkbox => {
            const itemElement = checkbox.closest('.wishlist-item');
            const removeBtn = itemElement?.querySelector('.remove-from-wishlist-btn');
            return removeBtn?.dataset.productId;
        }).filter(id => id);

        if (productIds.length === 0) {
            if (window.showToast) {
                window.showToast('No items selected', 'info');
            }
            return;
        }

        if (!confirm(`Are you sure you want to remove ${productIds.length} items from your wishlist?`)) {
            return;
        }

        try {
            // Remove each selected item
            for (const productId of productIds) {
                const response = await fetch(`/api/wishlist/api/remove/${productId}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': this.getCSRFToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (!response.ok) {
                    throw new Error(`Failed to remove item ${productId}`);
                }
            }

            if (window.showToast) {
                window.showToast(`Removed ${productIds.length} items from wishlist`, 'success');
            }
            
            // Remove selected items from DOM
            selectedItems.forEach(checkbox => {
                const itemElement = checkbox.closest('.wishlist-item');
                if (itemElement) {
                    itemElement.remove();
                }
            });
            
            this.updateWishlistEmptyState();
            this.loadWishlistPage(); // Reload to get updated stats
            this.loadWishlistCount();
            this.clearSelection();
            
        } catch (error) {
            console.error('Remove selected error:', error);
            if (window.showToast) {
                window.showToast('Failed to remove selected items', 'error');
            }
        }
    }

    clearSelection() {
        document.querySelectorAll('.wishlist-item-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        const bulkActions = document.getElementById('bulk-actions');
        if (bulkActions) {
            bulkActions.classList.add('hidden');
        }
    }

    updateWishlistEmptyState() {
        const container = document.getElementById('wishlist-items-container');
        const emptyState = document.getElementById('wishlist-empty-state');
        const bulkActions = document.getElementById('bulk-actions');
        
        if (container && emptyState) {
            const hasItems = container.querySelector('.wishlist-item');
            if (!hasItems) {
                emptyState.classList.remove('hidden');
                if (bulkActions) bulkActions.classList.add('hidden');
            } else {
                emptyState.classList.add('hidden');
            }
        }
    }

    updateWishlistStats(items = []) {
        const itemCount = document.getElementById('wishlist-item-count');
        const totalValue = document.getElementById('wishlist-total-value');
        const availableItems = document.getElementById('wishlist-available-items');
        
        if (itemCount) {
            itemCount.textContent = items.length;
        }
        
        if (totalValue) {
            // Calculate total value safely
            const total = items.reduce((sum, item) => {
                const product = item.product || item;
                const price = parseFloat(product.price) || 0;
                return sum + price;
            }, 0);
            totalValue.textContent = `$${total.toFixed(2)}`;
        }
        
        if (availableItems) {
            // Count available items (assuming all are available for now)
            const available = items.length;
            availableItems.textContent = available;
        }
    }

    async shareWishlist() {
        try {
            const response = await fetch('/api/wishlist/api/share/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    expires_in: 7 // days
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (window.showToast) {
                    window.showToast('Wishlist shared! Copy the URL to share.', 'success');
                }
                
                // Copy to clipboard
                if (navigator.clipboard && data.share_url) {
                    await navigator.clipboard.writeText(data.share_url);
                    if (window.showToast) {
                        window.showToast('Share URL copied to clipboard!', 'success');
                    }
                }
            } else {
                throw new Error('Failed to share wishlist');
            }
        } catch (error) {
            console.error('Share wishlist error:', error);
            if (window.showToast) {
                window.showToast('Failed to share wishlist', 'error');
            }
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

// Initialize wishlist manager
document.addEventListener('DOMContentLoaded', function() {
    window.wishlistManager = new WishlistManager();
});