class ProductManager {
    constructor() {
        this.filters = {};
        this.sortBy = 'name';
        this.currentPage = 1;
        this.initEventListeners();
        this.initInfiniteScroll();
    }

    initEventListeners() {
        // Filter changes
        document.addEventListener('change', (e) => {
            if (e.target.matches('.product-filter')) {
                this.handleFilterChange(e.target);
            }
        });

        // Sort changes
        document.addEventListener('change', (e) => {
            if (e.target.id === 'product-sort') {
                this.sortBy = e.target.value;
                this.loadProducts();
            }
        });

        // Search form
        document.addEventListener('submit', (e) => {
            if (e.target.id === 'product-search-form') {
                e.preventDefault();
                this.handleSearch(e.target);
            }
        });

        // Quick view
        document.addEventListener('click', (e) => {
            if (e.target.closest('.quick-view-btn')) {
                this.showQuickView(e.target.closest('.quick-view-btn'));
            }
        });

        // Product image zoom
        document.addEventListener('mouseenter', (e) => {
            if (e.target.classList.contains('product-image-zoom')) {
                this.initImageZoom(e.target);
            }
        }, { passive: true });
    }

    initInfiniteScroll() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadMoreProducts();
                }
            });
        });

        const sentinel = document.getElementById('load-more-sentinel');
        if (sentinel) {
            observer.observe(sentinel);
        }
    }

    handleFilterChange(filter) {
        const filterName = filter.name;
        const filterValue = filter.value;

        if (filterValue === '') {
            delete this.filters[filterName];
        } else {
            this.filters[filterName] = filterValue;
        }

        this.currentPage = 1;
        this.loadProducts();
    }

    handleSearch(form) {
        const formData = new FormData(form);
        const query = formData.get('q');

        if (query) {
            this.filters.search = query;
        } else {
            delete this.filters.search;
        }

        this.currentPage = 1;
        this.loadProducts();
    }

    async loadProducts() {
        const productsContainer = document.getElementById('products-container');
        if (!productsContainer) return;

        const loadingEl = document.getElementById('products-loading');
        if (loadingEl) loadingEl.style.display = 'block';

        const params = new URLSearchParams({
            page: this.currentPage,
            sort: this.sortBy,
            ...this.filters
        });

        const response = await ajaxUtils.makeRequest(`/api/products/?${params}`);

        if (response.success) {
            if (this.currentPage === 1) {
                productsContainer.innerHTML = this.renderProducts(response.data.results);
            } else {
                productsContainer.innerHTML += this.renderProducts(response.data.results);
            }

            this.updatePagination(response.data);
        } else {
            ajaxUtils.showMessage('Failed to load products', 'error');
        }

        if (loadingEl) loadingEl.style.display = 'none';
    }

    async loadMoreProducts() {
        this.currentPage++;
        await this.loadProducts();
    }

    renderProducts(products) {
        if (!products || products.length === 0) {
            return `
                <div class="col-span-full text-center py-12">
                    <i class="fas fa-search text-gray-400 text-4xl mb-4"></i>
                    <h3 class="text-xl font-semibold text-gray-600">No products found</h3>
                    <p class="text-gray-500 mt-2">Try adjusting your filters or search terms</p>
                </div>
            `;
        }

        return products.map(product => `
            <div class="product-card bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
                <div class="relative">
                    <img src="${product.primary_image || '/static/images/placeholder.jpg'}" 
                         alt="${product.name}"
                         class="w-full h-48 object-cover product-image-zoom">
                    
                    <div class="absolute top-2 right-2 flex space-x-1">
                        ${product.is_featured ? `
                            <span class="featured-badge bg-yellow-500 text-white px-2 py-1 rounded text-xs">
                                <i class="fas fa-star mr-1"></i>Featured
                            </span>
                        ` : ''}
                        
                        ${!product.is_in_stock ? `
                            <span class="out-of-stock-badge bg-red-500 text-white px-2 py-1 rounded text-xs">
                                Out of Stock
                            </span>
                        ` : ''}
                    </div>

                    <div class="absolute bottom-2 left-2 right-2 flex justify-between opacity-0 hover:opacity-100 transition-opacity duration-300">
                        <button class="quick-view-btn bg-white text-gray-800 p-2 rounded-full shadow-md hover:bg-gray-100"
                                data-product-id="${product.id}">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="add-to-wishlist-btn bg-white text-gray-800 p-2 rounded-full shadow-md hover:bg-gray-100"
                                data-product-id="${product.id}">
                            <i class="far fa-heart"></i>
                        </button>
                    </div>
                </div>

                <div class="p-4">
                    <h3 class="font-semibold text-lg mb-2 truncate">${product.name}</h3>
                    
                    <div class="flex items-center mb-2">
                        <div class="rating-stars text-yellow-400">
                            ${this.renderRatingStars(product.average_rating)}
                        </div>
                        <span class="text-sm text-gray-600 ml-2">
                            (${product.review_count || 0})
                        </span>
                    </div>

                    <div class="price-section mb-3">
                        <span class="current-price text-xl font-bold text-green-600">
                            $${product.price}
                        </span>
                        ${product.compare_price > product.price ? `
                            <span class="original-price text-sm text-gray-500 line-through ml-2">
                                $${product.compare_price}
                            </span>
                            <span class="discount-percent bg-red-100 text-red-800 text-xs px-1 rounded ml-2">
                                ${Math.round((1 - product.price / product.compare_price) * 100)}% OFF
                            </span>
                        ` : ''}
                    </div>

                    <div class="flex space-x-2">
                        <button class="add-to-cart-btn flex-1 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                                data-product-id="${product.id}"
                                ${!product.is_in_stock ? 'disabled' : ''}>
                            <i class="fas fa-shopping-cart mr-2"></i>
                            ${product.is_in_stock ? 'Add to Cart' : 'Out of Stock'}
                        </button>
                        
                        <button class="wishlist-toggle-btn bg-gray-200 text-gray-700 p-2 rounded hover:bg-gray-300 transition-colors"
                                data-product-id="${product.id}">
                            <i class="far fa-heart"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderRatingStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

        let stars = '';
        
        // Full stars
        for (let i = 0; i < fullStars; i++) {
            stars += '<i class="fas fa-star"></i>';
        }
        
        // Half star
        if (hasHalfStar) {
            stars += '<i class="fas fa-star-half-alt"></i>';
        }
        
        // Empty stars
        for (let i = 0; i < emptyStars; i++) {
            stars += '<i class="far fa-star"></i>';
        }
        
        return stars;
    }

    async showQuickView(button) {
        const productId = button.dataset.productId;
        const response = await ajaxUtils.makeRequest(`/api/products/${productId}/`);

        if (response.success) {
            this.openQuickViewModal(response.data);
        } else {
            ajaxUtils.showMessage('Failed to load product details', 'error');
        }
    }

    openQuickViewModal(product) {
        // Create or update quick view modal
        let modal = document.getElementById('quick-view-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'quick-view-modal';
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 hidden';
            modal.innerHTML = `
                <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                    <div class="modal-content relative">
                        <button class="absolute top-4 right-4 text-gray-500 hover:text-gray-700 z-10 close-quick-view">
                            <i class="fas fa-times text-2xl"></i>
                        </button>
                        <div id="quick-view-content"></div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            // Close modal handlers
            modal.querySelector('.close-quick-view').addEventListener('click', () => {
                modal.classList.add('hidden');
            });
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.add('hidden');
                }
            });
        }

        const content = modal.querySelector('#quick-view-content');
        content.innerHTML = this.renderQuickViewContent(product);

        modal.classList.remove('hidden');
    }

    renderQuickViewContent(product) {
        return `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
                <div class="product-images">
                    <div class="main-image mb-4">
                        <img src="${product.primary_image}" alt="${product.name}" 
                             class="w-full h-80 object-cover rounded-lg">
                    </div>
                    <div class="image-thumbnails flex space-x-2 overflow-x-auto">
                        ${product.images.map(image => `
                            <img src="${image.image}" alt="${image.alt_text}" 
                                 class="thumbnail w-16 h-16 object-cover rounded cursor-pointer border-2 border-transparent hover:border-blue-500">
                        `).join('')}
                    </div>
                </div>
                
                <div class="product-details">
                    <h1 class="text-2xl font-bold mb-2">${product.name}</h1>
                    
                    <div class="rating-section mb-4">
                        <div class="flex items-center">
                            <div class="rating-stars text-yellow-400 text-lg">
                                ${this.renderRatingStars(product.average_rating)}
                            </div>
                            <span class="ml-2 text-gray-600">
                                ${product.average_rating.toFixed(1)} (${product.review_count} reviews)
                            </span>
                        </div>
                    </div>
                    
                    <div class="price-section mb-4">
                        <span class="current-price text-3xl font-bold text-green-600">
                            $${product.price}
                        </span>
                        ${product.compare_price > product.price ? `
                            <span class="original-price text-xl text-gray-500 line-through ml-2">
                                $${product.compare_price}
                            </span>
                        ` : ''}
                    </div>
                    
                    <div class="description mb-6">
                        <p class="text-gray-700">${product.short_description || product.description}</p>
                    </div>
                    
                    <div class="action-buttons space-y-3">
                        ${product.variants.length > 0 ? `
                            <div class="variant-selector">
                                <label class="block text-sm font-medium text-gray-700 mb-2">Options:</label>
                                <select class="variant-select w-full p-2 border border-gray-300 rounded">
                                    ${product.variants.map(variant => `
                                        <option value="${variant.id}" 
                                                ${variant.quantity > 0 ? '' : 'disabled'}>
                                            ${variant.name} - $${variant.price}
                                            ${variant.quantity > 0 ? '' : '(Out of Stock)'}
                                        </option>
                                    `).join('')}
                                </select>
                            </div>
                        ` : ''}
                        
                        <div class="quantity-selector flex items-center space-x-4">
                            <label class="text-sm font-medium text-gray-700">Quantity:</label>
                            <div class="flex items-center border border-gray-300 rounded">
                                <button class="decrease-qty px-3 py-1 text-gray-600 hover:bg-gray-100">-</button>
                                <input type="number" value="1" min="1" max="${product.quantity}" 
                                       class="quantity-input w-16 text-center border-0 focus:ring-0">
                                <button class="increase-qty px-3 py-1 text-gray-600 hover:bg-gray-100">+</button>
                            </div>
                            <span class="text-sm text-gray-500">
                                ${product.quantity} available
                            </span>
                        </div>
                        
                        <div class="flex space-x-3">
                            <button class="add-to-cart-quickview flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors font-semibold"
                                    data-product-id="${product.id}">
                                <i class="fas fa-shopping-cart mr-2"></i>
                                Add to Cart
                            </button>
                            <button class="add-to-wishlist-quickview bg-gray-200 text-gray-700 p-3 rounded-lg hover:bg-gray-300 transition-colors"
                                    data-product-id="${product.id}">
                                <i class="far fa-heart"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    initImageZoom(image) {
        // Simple image zoom on hover
        image.addEventListener('mousemove', (e) => {
            const rect = image.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            
            image.style.transformOrigin = `${x}% ${y}%`;
            image.style.transform = 'scale(1.5)';
        });

        image.addEventListener('mouseleave', () => {
            image.style.transform = 'scale(1)';
        });
    }

    updatePagination(data) {
        const pagination = document.getElementById('products-pagination');
        if (!pagination || !data.pagination) return;

        const { current_page, total_pages, has_next, has_previous } = data.pagination;

        pagination.innerHTML = `
            <div class="flex justify-center items-center space-x-2">
                <button class="pagination-btn ${!has_previous ? 'opacity-50 cursor-not-allowed' : ''}"
                        ${has_previous ? `onclick="productManager.goToPage(${current_page - 1})"` : 'disabled'}>
                    <i class="fas fa-chevron-left"></i> Previous
                </button>
                
                <span class="px-4 py-2 text-sm text-gray-600">
                    Page ${current_page} of ${total_pages}
                </span>
                
                <button class="pagination-btn ${!has_next ? 'opacity-50 cursor-not-allowed' : ''}"
                        ${has_next ? `onclick="productManager.goToPage(${current_page + 1})"` : 'disabled'}>
                    Next <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadProducts();
        
        // Scroll to top of products
        const productsContainer = document.getElementById('products-container');
        if (productsContainer) {
            productsContainer.scrollIntoView({ behavior: 'smooth' });
        }
    }
}

// Global instance
const productManager = new ProductManager();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    productManager.loadProducts();
});