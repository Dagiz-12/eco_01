// static/js/navigation.js
class NavigationManager {
    constructor() {
        this.initEventListeners();
        this.loadDynamicCounts();
    }

    initEventListeners() {
        // Search functionality
        const searchForm = document.querySelector('form[action*="search"]');
        if (searchForm) {
            searchForm.addEventListener('submit', this.handleSearch.bind(this));
        }

        // Mobile menu toggle
        this.initMobileMenu();
    }

    handleSearch(e) {
        const searchInput = e.target.querySelector('input[name="q"]');
        if (searchInput.value.trim().length < 2) {
            e.preventDefault();
            this.showMessage('Please enter at least 2 characters to search', 'warning');
        }
    }

    async loadDynamicCounts() {
        await this.loadCartCount();
        await this.loadWishlistCount();
        await this.loadCategoriesDropdown();
    }

    async loadCartCount() {
        try {
            const response = await fetch('/api/cart/');
            if (response.ok) {
                const data = await response.json();
                this.updateCounter('cart-count', data.total_items || 0);
            }
        } catch (error) {
            console.error('Failed to load cart count:', error);
        }
    }

    async loadWishlistCount() {
        try {
            const response = await fetch('/api/wishlist/');
            if (response.ok) {
                const data = await response.json();
                this.updateCounter('wishlist-count', data.item_count || 0);
            }
        } catch (error) {
            console.error('Failed to load wishlist count:', error);
        }
    }

    async loadCategoriesDropdown() {
        try {
            const response = await fetch('/api/home/categories/');
            if (response.ok) {
                const data = await response.json();
                this.renderCategoriesDropdown(data.categories);
            }
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }

    renderCategoriesDropdown(categories) {
        const dropdown = document.getElementById('categories-dropdown');
        if (!dropdown || !categories) return;

        // Clear existing items except "All Categories"
        const allCategoriesLink = dropdown.querySelector('a[href*="products"]');
        dropdown.innerHTML = '';
        if (allCategoriesLink) {
            dropdown.appendChild(allCategoriesLink);
        }

        // Add categories
        categories.slice(0, 8).forEach(category => {
            const link = document.createElement('a');
            link.href = `/products/?category=${category.id}`;
            link.className = 'block px-4 py-2 text-gray-700 hover:bg-gray-100 transition-colors';
            link.textContent = category.name;
            dropdown.appendChild(link);
        });
    }

    updateCounter(elementId, count) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = count;
            if (count > 0) {
                element.classList.remove('hidden');
                // Add animation
                element.classList.add('animate-pulse');
                setTimeout(() => element.classList.remove('animate-pulse'), 1000);
            } else {
                element.classList.add('hidden');
            }
        }
    }

    initMobileMenu() {
        // Add mobile menu functionality if needed
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        
        if (mobileMenuButton && mobileMenu) {
            mobileMenuButton.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });
        }
    }

    showMessage(message, type = 'info') {
        // Use existing ajaxUtils or create simple notification
        if (typeof ajaxUtils !== 'undefined') {
            ajaxUtils.showMessage(message, type);
        } else {
            // Simple notification fallback
            const container = document.getElementById('messages-container');
            if (container) {
                const messageEl = document.createElement('div');
                messageEl.className = `bg-${type === 'error' ? 'red' : type === 'success' ? 'green' : 'blue'}-500 text-white p-4 rounded-lg shadow-lg`;
                messageEl.textContent = message;
                container.appendChild(messageEl);
                
                setTimeout(() => {
                    if (messageEl.parentElement) {
                        messageEl.remove();
                    }
                }, 5000);
            }
        }
    }
}

// Initialize navigation manager
document.addEventListener('DOMContentLoaded', function() {
    new NavigationManager();
});