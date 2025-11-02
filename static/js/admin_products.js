// Enhanced Products Management JavaScript - COMPLETE VERSION
class ProductsManager {
    constructor() {
        this.currentView = 'grid';
        this.currentPage = 1;
        this.filters = {
            search: '',
            category: '',
            brand: '',
            status: '',
            stock: '',
            price: '',
            sort: 'newest'
        };
        this.selectedProducts = new Set();
        this.categories = [];
        this.brands = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadFiltersData();
        this.loadProducts();
        this.loadProductStats();
    }

    setupEventListeners() {
        // Search input with debounce
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => {
                this.filters.search = searchInput.value;
                this.currentPage = 1;
                this.loadProducts();
            }, 500));
        }

        // Filter changes
        ['category-filter', 'brand-filter', 'status-filter', 'stock-filter', 'price-filter', 'sort-by'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', (e) => {
                    const filterKey = id.replace('-filter', '').replace('-by', '');
                    this.filters[filterKey] = e.target.value;
                    this.currentPage = 1;
                    this.loadProducts();
                    this.updateActiveFilters();
                });
            }
        });

        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            const productModal = document.getElementById('product-modal');
            const quickEditModal = document.getElementById('quick-edit-modal');
            const importModal = document.getElementById('import-modal');
            
            if (productModal && !productModal.contains(e.target) && !e.target.closest('[onclick*="viewProductDetails"]')) {
            this.closeProductModal();
        }
        if (quickEditModal && !quickEditModal.contains(e.target) && !e.target.closest('[onclick*="quickEditProduct"]')) {
            this.closeQuickEditModal();
        }
        if (importModal && !importModal.contains(e.target) && !e.target.closest('[onclick*="showImportModal"]')) {
            this.closeImportModal();
        }
        });

         // Close on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            this.closeProductModal();
            this.closeQuickEditModal();
            this.closeImportModal();
        }
    });

    }

    async loadFiltersData() {
        try {
            // Load categories
            const categoriesResponse = await fetch('/api/categories/');
            if (categoriesResponse.ok) {
                this.categories = await categoriesResponse.json();
                this.populateCategoryFilter();
            }

            // Load brands
            const brandsResponse = await fetch('/api/brands/');
            if (brandsResponse.ok) {
                this.brands = await brandsResponse.json();
                this.populateBrandFilter();
            }
        } catch (error) {
            console.error('Failed to load filters data:', error);
        }
    }

    populateCategoryFilter() {
        const categoryFilter = document.getElementById('category-filter');
        if (categoryFilter && this.categories.length > 0) {
            categoryFilter.innerHTML = '<option value="">All Categories</option>' +
                this.categories.map(cat => 
                    `<option value="${cat.id}">${cat.name}</option>`
                ).join('');
        }
    }

    populateBrandFilter() {
        const brandFilter = document.getElementById('brand-filter');
        if (brandFilter && this.brands.length > 0) {
            brandFilter.innerHTML = '<option value="">All Brands</option>' +
                this.brands.map(brand => 
                    `<option value="${brand.id}">${brand.name}</option>`
                ).join('');
        }
    }

    async loadProductStats() {
        try {
            const response = await fetch('/admin-dashboard/api/products/stats/');
            if (response.ok) {
                const stats = await response.json();
                this.updateStatsDisplay(stats);
            }
        } catch (error) {
            console.error('Failed to load product stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        const elements = {
            'total-products': stats.total_products || 0,
            'published-products': stats.published_products || 0,
            'low-stock-products': stats.low_stock_products || 0,
            'out-of-stock-products': stats.out_of_stock_products || 0
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }

    async loadProducts() {
        try {
            const queryString = this.buildQueryString();
            const response = await fetch(`/admin-dashboard/api/products/enhanced/${queryString}`);
            
            if (response.ok) {
                const data = await response.json();
                this.renderProducts(data);
                this.updateResultsCount(data);
            } else {
                throw new Error('Failed to fetch products');
            }
        } catch (error) {
            console.error('Failed to load products:', error);
            showToast('Failed to load products: ' + error.message, 'error');
        }
    }

    buildQueryString() {
        const params = new URLSearchParams();
        params.append('page', this.currentPage);
        
        Object.entries(this.filters).forEach(([key, value]) => {
            if (value) params.append(key, value);
        });
        
        return `?${params.toString()}`;
    }

    renderProducts(data) {
        if (this.currentView === 'grid') {
            this.renderGridView(data.products);
        } else {
            this.renderTableView(data.products);
        }
        
        this.renderPagination(data.pagination);
    }

    renderGridView(products) {
        const container = document.getElementById('products-grid-view');
        
        if (!products || products.length === 0) {
            container.innerHTML = this.getEmptyStateHTML('products');
            return;
        }

        container.innerHTML = products.map(product => `
            <div class="bg-white rounded-lg shadow-md overflow-hidden product-card" data-product-id="${product.id}">
                <div class="h-48 bg-gray-200 flex items-center justify-center relative">
                    ${product.primary_image ? 
                        `<img src="${product.primary_image}" alt="${product.name}" class="h-full w-full object-cover">` :
                        `<div class="text-center text-gray-400">
                            <i class="fas fa-image text-4xl mb-2"></i>
                            <p class="text-sm">No Image</p>
                        </div>`
                    }
                    <div class="absolute top-2 right-2">
                        <input type="checkbox" value="${product.id}" onchange="productsManager.toggleProductSelection(${product.id})" class="product-checkbox">
                    </div>
                    ${product.is_featured ? `
                        <div class="absolute top-2 left-2 bg-yellow-500 text-white px-2 py-1 rounded text-xs font-semibold">
                            <i class="fas fa-star mr-1"></i>Featured
                        </div>
                    ` : ''}
                </div>
                <div class="p-4">
                    <div class="flex justify-between items-start mb-2">
                        <h3 class="font-semibold text-lg truncate flex-1 mr-2">${product.name}</h3>
                        <span class="text-green-600 font-bold">$${product.price}</span>
                    </div>
                    
                    <div class="flex items-center justify-between text-sm text-gray-600 mb-3">
                        <span>${product.category_name || 'No category'}</span>
                        <span>${product.brand_name || 'No brand'}</span>
                    </div>
                    
                    <div class="flex justify-between items-center mb-3">
                        <span class="text-sm ${this.getStockStatusClass(product)}">
                            ${this.getStockStatusText(product)}
                        </span>
                        <span class="text-sm text-gray-600">
                            ${product.total_sold || 0} sold
                        </span>
                    </div>
                    
                    <div class="flex space-x-2">
                        <button onclick="productsManager.quickEditProduct(${product.id})" 
                                class="flex-1 bg-blue-600 text-white py-2 px-3 rounded text-sm hover:bg-blue-700">
                            <i class="fas fa-edit mr-1"></i>Edit
                        </button>
                        <button onclick="productsManager.toggleProductStatus(${product.id}, '${product.status}')" 
                                class="flex-1 ${product.status === 'published' ? 'bg-red-600' : 'bg-green-600'} text-white py-2 px-3 rounded text-sm hover:${product.status === 'published' ? 'bg-red-700' : 'bg-green-700'}">
                            <i class="fas ${product.status === 'published' ? 'fa-eye-slash' : 'fa-eye'} mr-1"></i>
                            ${product.status === 'published' ? 'Unpublish' : 'Publish'}
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderTableView(products) {
        const tbody = document.getElementById('products-table-body');
        
        if (!products || products.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="px-6 py-8 text-center text-gray-500">${this.getEmptyStateHTML('products')}</td></tr>`;
            return;
        }

        tbody.innerHTML = products.map(product => `
            <tr class="hover:bg-gray-50" data-product-id="${product.id}">
                <td class="px-6 py-4 whitespace-nowrap">
                    <input type="checkbox" value="${product.id}" onchange="productsManager.toggleProductSelection(${product.id})" class="product-checkbox">
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10 bg-gray-300 rounded flex items-center justify-center mr-3">
                            ${product.primary_image ? 
                                `<img src="${product.primary_image}" alt="${product.name}" class="h-10 w-10 object-cover rounded">` :
                                `<i class="fas fa-cube text-gray-400"></i>`
                            }
                        </div>
                        <div>
                            <div class="text-sm font-medium text-gray-900">${product.name}</div>
                            <div class="text-sm text-gray-500">SKU: ${product.sku}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${product.category_name || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${product.brand_name || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    $${product.price}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="text-sm ${this.getStockStatusClass(product)}">
                        ${product.quantity || 0}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${this.getStatusClass(product)}">
                        ${product.status}
                    </span>
                    ${product.is_featured ? `
                        <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800 ml-1">
                            Featured
                        </span>
                    ` : ''}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${product.total_sold || 0}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="productsManager.viewProductDetails(${product.id})" class="text-blue-600 hover:text-blue-900 mr-3">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button onclick="productsManager.quickEditProduct(${product.id})" class="text-green-600 hover:text-green-900 mr-3">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="productsManager.toggleProductStatus(${product.id}, '${product.status}')" class="${product.status === 'published' ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}">
                        <i class="fas ${product.status === 'published' ? 'fa-eye-slash' : 'fa-eye'}"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    getStockStatusClass(product) {
        if (product.quantity === 0) {
            return 'text-red-600 font-semibold';
        } else if (product.low_stock) {
            return 'text-yellow-600 font-semibold';
        } else {
            return 'text-green-600';
        }
    }

    getStockStatusText(product) {
        if (product.quantity === 0) {
            return 'Out of Stock';
        } else if (product.low_stock) {
            return `Low Stock (${product.quantity})`;
        } else {
            return `In Stock (${product.quantity})`;
        }
    }

    getStatusClass(product) {
        switch (product.status) {
            case 'published':
                return 'bg-green-100 text-green-800';
            case 'draft':
                return 'bg-yellow-100 text-yellow-800';
            case 'archived':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    getEmptyStateHTML(type) {
        return `
            <div class="text-center py-12">
                <i class="fas fa-cube text-4xl text-gray-300 mb-4"></i>
                <p class="text-gray-600 text-lg mb-2">No ${type} found</p>
                <p class="text-gray-500">Try adjusting your filters or search terms</p>
            </div>
        `;
    }

    updateResultsCount(data) {
        const resultsCount = document.getElementById('results-count');
        if (resultsCount && data.pagination) {
            const start = ((data.pagination.page - 1) * data.pagination.page_size) + 1;
            const end = Math.min(data.pagination.page * data.pagination.page_size, data.pagination.total_count);
            resultsCount.textContent = `Showing ${start}-${end} of ${data.pagination.total_count} products`;
        }
    }

    renderPagination(pagination) {
        const container = document.getElementById('pagination');
        if (!container || !pagination) return;
        
        const totalPages = pagination.total_pages;
        const currentPage = pagination.page;
        
        container.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="text-sm text-gray-700">
                    Showing ${((currentPage - 1) * pagination.page_size) + 1} to ${Math.min(currentPage * pagination.page_size, pagination.total_count)} of ${pagination.total_count} products
                </div>
                <div class="flex space-x-2">
                    ${currentPage > 1 ? `
                        <button onclick="productsManager.goToPage(${currentPage - 1})" class="px-3 py-1 border rounded hover:bg-gray-50">
                            Previous
                        </button>
                    ` : ''}
                    
                    ${this.generatePaginationButtons(currentPage, totalPages)}
                    
                    ${currentPage < totalPages ? `
                        <button onclick="productsManager.goToPage(${currentPage + 1})" class="px-3 py-1 border rounded hover:bg-gray-50">
                            Next
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    generatePaginationButtons(currentPage, totalPages) {
        const buttons = [];
        const maxVisiblePages = 5;
        
        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
        
        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        for (let page = startPage; page <= endPage; page++) {
            buttons.push(`
                <button onclick="productsManager.goToPage(${page})" 
                        class="px-3 py-1 border rounded ${page === currentPage ? 'bg-blue-600 text-white' : 'hover:bg-gray-50'}">
                    ${page}
                </button>
            `);
        }
        
        return buttons.join('');
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadProducts();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Selection functions
    toggleProductSelection(productId) {
        const checkbox = document.querySelector(`.product-checkbox[value="${productId}"]`);
        if (checkbox.checked) {
            this.selectedProducts.add(productId);
        } else {
            this.selectedProducts.delete(productId);
            const selectAll = document.getElementById('select-all-products');
            if (selectAll) selectAll.checked = false;
        }
        this.updateBulkActions();
    }

    toggleSelectAllProducts() {
        const selectAll = document.getElementById('select-all-products');
        const checkboxes = document.querySelectorAll('.product-checkbox');
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAll.checked;
            if (selectAll.checked) {
                this.selectedProducts.add(parseInt(checkbox.value));
            } else {
                this.selectedProducts.delete(parseInt(checkbox.value));
            }
        });
        
        this.updateBulkActions();
    }

    updateBulkActions() {
        const bulkActions = document.getElementById('bulk-actions');
        if (bulkActions) {
            if (this.selectedProducts.size > 0) {
                bulkActions.style.display = 'flex';
            } else {
                bulkActions.style.display = 'none';
            }
        }
    }

    // View switching
    switchView(view) {
        this.currentView = view;
        
        const gridViewBtn = document.getElementById('grid-view-btn');
        const tableViewBtn = document.getElementById('table-view-btn');
        const gridView = document.getElementById('products-grid-view');
        const tableView = document.getElementById('products-table-view');
        
        if (view === 'grid') {
            if (gridViewBtn) gridViewBtn.className = 'px-4 py-2 bg-blue-600 text-white rounded-lg';
            if (tableViewBtn) tableViewBtn.className = 'px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300';
            if (gridView) gridView.classList.remove('hidden');
            if (tableView) tableView.classList.add('hidden');
        } else {
            if (gridViewBtn) gridViewBtn.className = 'px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300';
            if (tableViewBtn) tableViewBtn.className = 'px-4 py-2 bg-blue-600 text-white rounded-lg';
            if (gridView) gridView.classList.add('hidden');
            if (tableView) tableView.classList.remove('hidden');
        }
        
        this.loadProducts();
    }

    // Bulk actions
    async bulkPublishProducts() {
        if (this.selectedProducts.size === 0) return;
        
        if (!confirm(`Publish ${this.selectedProducts.size} product(s)?`)) return;
        
        try {
            const response = await fetch('/admin-dashboard/api/products/bulk-actions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    action: 'publish',
                    product_ids: Array.from(this.selectedProducts)
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                showToast(result.message, 'success');
                this.selectedProducts.clear();
                this.updateBulkActions();
                this.loadProducts();
                this.loadProductStats();
            }
        } catch (error) {
            console.error('Failed to bulk publish products:', error);
            showToast('Failed to publish products', 'error');
        }
    }

    async bulkUnpublishProducts() {
        if (this.selectedProducts.size === 0) return;
        
        if (!confirm(`Unpublish ${this.selectedProducts.size} product(s)?`)) return;
        
        try {
            const response = await fetch('/admin-dashboard/api/products/bulk-actions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    action: 'unpublish',
                    product_ids: Array.from(this.selectedProducts)
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                showToast(result.message, 'success');
                this.selectedProducts.clear();
                this.updateBulkActions();
                this.loadProducts();
                this.loadProductStats();
            }
        } catch (error) {
            console.error('Failed to bulk unpublish products:', error);
            showToast('Failed to unpublish products', 'error');
        }
    }

    async bulkDeleteProducts() {
        if (this.selectedProducts.size === 0) return;
        
        if (!confirm(`Delete ${this.selectedProducts.size} product(s)? This action cannot be undone.`)) return;
        
        try {
            const response = await fetch('/admin-dashboard/api/products/bulk-actions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    action: 'delete',
                    product_ids: Array.from(this.selectedProducts)
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                showToast(result.message, 'success');
                this.selectedProducts.clear();
                this.updateBulkActions();
                this.loadProducts();
                this.loadProductStats();
            }
        } catch (error) {
            console.error('Failed to bulk delete products:', error);
            showToast('Failed to delete products', 'error');
        }
    }

    // Product actions
    async viewProductDetails(productId) {
        try {
            const response = await fetch(`/admin-dashboard/api/products/${productId}/`);
            if (response.ok) {
                const product = await response.json();
                this.showProductModal(product);
            }
        } catch (error) {
            console.error('Failed to load product details:', error);
            showToast('Failed to load product details', 'error');
        }
    }

    async quickEditProduct(productId) {
        try {
            const response = await fetch(`/admin-dashboard/api/products/${productId}/`);
            if (response.ok) {
                const product = await response.json();
                this.showQuickEditModal(product);
            }
        } catch (error) {
            console.error('Failed to load product for editing:', error);
            showToast('Failed to load product', 'error');
        }
    }

    async toggleProductStatus(productId, currentStatus) {
        const newStatus = currentStatus === 'published' ? 'draft' : 'published';
        const action = currentStatus === 'published' ? 'unpublish' : 'publish';
        
        if (!confirm(`Are you sure you want to ${action} this product?`)) return;
        
        try {
            const response = await fetch(`/admin-dashboard/api/products/${productId}/inventory/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    action: 'update_status',
                    status: newStatus
                })
            });
            
            if (response.ok) {
                showToast(`Product ${action}ed successfully`, 'success');
                this.loadProducts();
                this.loadProductStats();
            }
        } catch (error) {
            console.error(`Failed to ${action} product:`, error);
            showToast(`Failed to ${action} product`, 'error');
        }
    }

    // Modal functions
    showProductModal(product) {
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('product-modal-content');
        
        if (modalTitle) modalTitle.textContent = `Product: ${product.name}`;
        if (modalContent) modalContent.innerHTML = this.getProductModalHTML(product);
        
        document.getElementById('product-modal').classList.remove('hidden');
    }

    showQuickEditModal(product) {
        const quickEditContent = document.getElementById('quick-edit-content');
        if (quickEditContent) {
            quickEditContent.innerHTML = this.getQuickEditFormHTML(product);
        }
        document.getElementById('quick-edit-modal').classList.remove('hidden');
    }

    closeProductModal() {
        document.getElementById('product-modal').classList.add('hidden');
    }

    closeQuickEditModal() {
        document.getElementById('quick-edit-modal').classList.add('hidden');
    }

    showImportModal() {
        document.getElementById('import-modal').classList.remove('hidden');
    }

    closeImportModal() {
        document.getElementById('import-modal').classList.add('hidden');
    }

    async importProducts() {
        const fileInput = document.getElementById('csv-file');
        if (!fileInput.files.length) {
            showToast('Please select a CSV file', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('csv_file', fileInput.files[0]);

        try {
            const response = await fetch('/admin-dashboard/api/products/import/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                },
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                showToast(result.message, 'success');
                this.closeImportModal();
                this.loadProducts();
                this.loadProductStats();
            } else {
                throw new Error('Import failed');
            }
        } catch (error) {
            console.error('Failed to import products:', error);
            showToast('Failed to import products', 'error');
        }
    }

    // Utility functions
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    updateActiveFilters() {
        const activeFiltersContainer = document.getElementById('active-filters');
        const activeFilters = Object.entries(this.filters).filter(([key, value]) => value && key !== 'sort');
        
        if (!activeFiltersContainer) return;
        
        if (activeFilters.length === 0) {
            activeFiltersContainer.classList.add('hidden');
            return;
        }
        
        activeFiltersContainer.classList.remove('hidden');
        activeFiltersContainer.innerHTML = activeFilters.map(([key, value]) => {
            let displayValue = value;
            let displayKey = key.charAt(0).toUpperCase() + key.slice(1);
            
            // Format display values
            if (key === 'price') {
                displayValue = this.formatPriceRange(value);
            } else if (key === 'stock') {
                displayValue = this.formatStockStatus(value);
            } else if (key === 'status') {
                displayValue = value.charAt(0).toUpperCase() + value.slice(1);
            }
            
            return `
                <div class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center">
                    <span>${displayKey}: ${displayValue}</span>
                    <button onclick="productsManager.removeFilter('${key}')" class="ml-2 text-blue-600 hover:text-blue-800">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        }).join('');
    }

    removeFilter(filterKey) {
        this.filters[filterKey] = '';
        
        // Reset the corresponding form element
        const element = document.getElementById(`${filterKey}-filter`);
        if (element) {
            element.value = '';
        }
        
        this.currentPage = 1;
        this.loadProducts();
        this.updateActiveFilters();
    }

    formatPriceRange(priceRange) {
        const ranges = {
            '0-50': '$0 - $50',
            '50-100': '$50 - $100',
            '100-500': '$100 - $500',
            '500+': '$500+'
        };
        return ranges[priceRange] || priceRange;
    }

    formatStockStatus(stockStatus) {
        const statuses = {
            'in_stock': 'In Stock',
            'low_stock': 'Low Stock',
            'out_of_stock': 'Out of Stock'
        };
        return statuses[stockStatus] || stockStatus;
    }

    // Export function
    exportProducts() {
        const queryString = this.buildQueryString().replace('?', '');
        const url = `/admin-dashboard/api/products/export/${queryString ? '?' + queryString : ''}`;
        
        // Create a temporary link to trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = 'products_export.csv';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showToast('Export started...', 'info');
    }

    // Quick edit form handler
    async handleQuickEdit(event, productId) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());

    // Convert numeric fields
    if (data.price) data.price = parseFloat(data.price);
    if (data.compare_price) data.compare_price = parseFloat(data.compare_price);
    if (data.quantity) data.quantity = parseInt(data.quantity);
    data.is_featured = data.is_featured === 'on';

    try {
        const response = await fetch(`/admin-dashboard/api/products/${productId}/quick-edit/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const result = await response.json();
            showToast(result.message, 'success');
            this.closeQuickEditModal();
            this.loadProducts();
            this.loadProductStats();
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Failed to update product');
        }
    } catch (error) {
        console.error('Failed to update product:', error);
        showToast('Failed to update product: ' + error.message, 'error');
    }
}

    // Modal HTML generators
    getProductModalHTML(product) {
        return `
            <div class="space-y-6">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                        <h4 class="font-semibold mb-3">Basic Information</h4>
                        <div class="space-y-2">
                            <p><strong>Name:</strong> ${product.name}</p>
                            <p><strong>SKU:</strong> ${product.sku}</p>
                            <p><strong>Description:</strong> ${product.description || 'No description'}</p>
                            <p><strong>Category:</strong> ${product.category_name || 'No category'}</p>
                            <p><strong>Brand:</strong> ${product.brand_name || 'No brand'}</p>
                        </div>
                    </div>
                    <div>
                        <h4 class="font-semibold mb-3">Pricing & Inventory</h4>
                        <div class="space-y-2">
                            <p><strong>Price:</strong> $${product.price}</p>
                            <p><strong>Compare Price:</strong> $${product.compare_price || 'N/A'}</p>
                            <p><strong>Cost Price:</strong> $${product.cost_per_item || 'N/A'}</p>
                            <p><strong>Stock:</strong> ${product.quantity} units</p>
                            <p><strong>Low Stock Threshold:</strong> ${product.low_stock_threshold} units</p>
                        </div>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                        <h4 class="font-semibold mb-3">Status & Metadata</h4>
                        <div class="space-y-2">
                            <p><strong>Status:</strong> <span class="capitalize">${product.status}</span></p>
                            <p><strong>Featured:</strong> ${product.is_featured ? 'Yes' : 'No'}</p>
                            <p><strong>Digital Product:</strong> ${product.is_digital ? 'Yes' : 'No'}</p>
                            <p><strong>Total Sold:</strong> ${product.total_sold} units</p>
                            <p><strong>Created:</strong> ${new Date(product.created_at).toLocaleString()}</p>
                        </div>
                    </div>
                    <div>
                        <h4 class="font-semibold mb-3">SEO Information</h4>
                        <div class="space-y-2">
                            <p><strong>Meta Title:</strong> ${product.meta_title || 'Not set'}</p>
                            <p><strong>Meta Description:</strong> ${product.meta_description || 'Not set'}</p>
                            <p><strong>Slug:</strong> ${product.slug}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getQuickEditFormHTML(product) {
        return `
            <form onsubmit="productsManager.handleQuickEdit(event, ${product.id})">
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Product Name</label>
                        <input type="text" name="name" value="${product.name}" 
                               class="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Price ($)</label>
                            <input type="number" name="price" value="${product.price}" step="0.01" min="0"
                                   class="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Compare Price ($)</label>
                            <input type="number" name="compare_price" value="${product.compare_price || ''}" step="0.01" min="0"
                                   class="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                            <input type="number" name="quantity" value="${product.quantity}" min="0"
                                   class="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
                            <select name="status" class="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                                <option value="draft" ${product.status === 'draft' ? 'selected' : ''}>Draft</option>
                                <option value="published" ${product.status === 'published' ? 'selected' : ''}>Published</option>
                                <option value="archived" ${product.status === 'archived' ? 'selected' : ''}>Archived</option>
                            </select>
                        </div>
                    </div>
                    
                    <div>
                        <label class="flex items-center">
                            <input type="checkbox" name="is_featured" ${product.is_featured ? 'checked' : ''} 
                                   class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                            <span class="ml-2 text-sm text-gray-700">Featured Product</span>
                        </label>
                    </div>
                    
                    <div class="flex justify-end space-x-3 pt-4">
                        <button type="button" onclick="productsManager.closeQuickEditModal()" 
                                class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
                            Cancel
                        </button>
                        <button type="submit" 
                                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                            Save Changes
                        </button>
                    </div>
                </div>
            </form>
        `;
    }


    showAddProductForm() {
    // Redirect to Django admin or show a form
    window.location.href = '/admin/products/product/add/';
}

}

// Utility functions
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue;
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white z-50 transform transition-transform duration-300 ${
        type === 'success' ? 'bg-green-600' :
        type === 'error' ? 'bg-red-600' :
        type === 'warning' ? 'bg-yellow-600' :
        'bg-blue-600'
    }`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.classList.add('translate-x-0');
    }, 10);
    
    // Remove after delay
    setTimeout(() => {
        toast.classList.remove('translate-x-0');
        toast.classList.add('translate-x-full');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.productsManager = new ProductsManager();
});

// Global functions for HTML onclick handlers
function showImportModal() {
    if (window.productsManager) {
        window.productsManager.showImportModal();
    }
}

function exportProducts() {
    if (window.productsManager) {
        window.productsManager.exportProducts();
    }
}

function switchView(view) {
    if (window.productsManager) {
        window.productsManager.switchView(view);
    }
}

function toggleSelectAllProducts() {
    if (window.productsManager) {
        window.productsManager.toggleSelectAllProducts();
    }
}

function bulkPublishProducts() {
    if (window.productsManager) {
        window.productsManager.bulkPublishProducts();
    }
}

function bulkUnpublishProducts() {
    if (window.productsManager) {
        window.productsManager.bulkUnpublishProducts();
    }
}

function bulkDeleteProducts() {
    if (window.productsManager) {
        window.productsManager.bulkDeleteProducts();
    }
}

// Add these global functions at the end of the file
function closeProductModal() {
    if (window.productsManager) {
        window.productsManager.closeProductModal();
    }
}

function closeQuickEditModal() {
    if (window.productsManager) {
        window.productsManager.closeQuickEditModal();
    }
}

function closeImportModal() {
    if (window.productsManager) {
        window.productsManager.closeImportModal();
    }
}


function showAddProductForm() {
    if (window.productsManager) {
        window.productsManager.showAddProductForm();
    }
}