// Enhanced Orders Management JavaScript
class OrdersManager {
    constructor() {
        this.currentPage = 1;
        this.filters = {
            search: '',
            status: '',
            payment_status: '',
            date_from: '',
            date_to: '',
            sort: 'newest'
        };
        this.selectedOrders = new Set();
        this.currentOrderId = null;

        this.init();
        
    }

    init() {
        this.setupEventListeners();
        this.loadOrders();
        this.loadOrderStats();
    }

    setupEventListeners() {
        // Search input with debounce
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => {
                this.filters.search = searchInput.value;
                this.currentPage = 1;
                this.loadOrders();
            }, 500));
        }

        // Filter changes
        ['status-filter', 'payment-status-filter', 'sort-by'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', (e) => {
                    const filterKey = id.replace('-filter', '').replace('-by', '');
                    this.filters[filterKey] = e.target.value;
                    this.currentPage = 1;
                    this.loadOrders();
                    this.updateActiveFilters();
                });
            }
        });

        // Date range filters
        const dateFrom = document.getElementById('date-from');
        const dateTo = document.getElementById('date-to');
        if (dateFrom) {
            dateFrom.addEventListener('change', (e) => {
                this.filters.date_from = e.target.value;
                this.currentPage = 1;
                this.loadOrders();
                this.updateActiveFilters();
            });
        }
        if (dateTo) {
            dateTo.addEventListener('change', (e) => {
                this.filters.date_to = e.target.value;
                this.currentPage = 1;
                this.loadOrders();
                this.updateActiveFilters();
            });
        }

        // Setup modal listeners
        this.setupModalListeners();
    }
setupModalListeners() {
    // Only setup essential listeners that won't interfere with onclick
    const orderModal = document.getElementById('order-modal');
    if (orderModal) {
        const closeButton = orderModal.querySelector('.close-modal-btn');
        if (closeButton) {
            closeButton.addEventListener('click', () => this.closeOrderModal());
        }
    }

    // Close modals when clicking outside (only for order modal)
    document.addEventListener('click', (e) => {
        const orderModal = document.getElementById('order-modal');
        if (orderModal && !orderModal.contains(e.target) && !e.target.closest('[onclick*="viewOrderDetails"]')) {
            this.closeOrderModal();
        }
    });

    // Escape key to close modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            this.closeOrderModal();
            this.closeStatusModal();
        }
    });
}

    async loadOrderStats() {
        try {
            const response = await fetch('/admin-dashboard/api/stats/');
            if (response.ok) {
                const stats = await response.json();
                this.updateStatsDisplay(stats);
            }
        } catch (error) {
            console.error('Failed to load order stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        const elements = {
            'total-orders': stats.total_orders || 0,
            'pending-orders': stats.pending_orders || 0,
            'completed-orders': this.calculateCompletedOrders(stats) || 0,
            'total-revenue': `$${(stats.total_revenue || 0).toFixed(2)}`
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }

    calculateCompletedOrders(stats) {
        // You might want to calculate completed orders differently
        // For now, we'll assume completed orders = total - pending
        return (stats.total_orders || 0) - (stats.pending_orders || 0);
    }

    async loadOrders() {
        try {
            const queryString = this.buildQueryString();
            const response = await fetch(`/admin-dashboard/api/orders/${queryString}`);

            if (response.ok) {
                const data = await response.json();
                this.renderOrders(data);
                this.updateResultsCount(data);
            } else {
                throw new Error('Failed to fetch orders');
            }
        } catch (error) {
            console.error('Failed to load orders:', error);
            showToast('Failed to load orders: ' + error.message, 'error');
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

    renderOrders(data) {
    const container = document.getElementById('orders-table-body');
    
    if (!data.orders || data.orders.length === 0) {
        container.innerHTML = this.getEmptyStateHTML('orders');
        return;
    }

    container.innerHTML = data.orders.map(order => `
        <tr class="hover:bg-gray-50" data-order-id="${order.id}">
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="checkbox" value="${order.id}" onchange="ordersManager.toggleOrderSelection(${order.id})" class="order-checkbox">
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                ${order.order_number}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                <div>
                    <div class="font-medium">${order.customer_name || 'N/A'}</div>
                    <div class="text-gray-500">${order.customer_email || 'N/A'}</div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                $${parseFloat(order.grand_total || 0).toFixed(2)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${this.getStatusClass(order)}">
                    ${order.status || 'pending'}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${this.getPaymentStatusClass(order)}">
                    ${order.payment_status || 'pending'}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${order.item_count || 0} items
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${new Date(order.created_at).toLocaleDateString()}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button onclick="ordersManager.viewOrderDetails(${order.id})" class="text-blue-600 hover:text-blue-900 mr-3" title="View Details">
                    <i class="fas fa-eye"></i>
                </button>
                <button onclick="ordersManager.showStatusModal(${order.id})" class="text-green-600 hover:text-green-900" title="Update Status">
                    <i class="fas fa-edit"></i>
                </button>
            </td>
        </tr>
    `).join('');

    this.renderPagination(data.pagination);
}

    getStatusClass(order) {
        const status = order.status || 'pending';
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800';
            case 'processing':
                return 'bg-blue-100 text-blue-800';
            case 'pending':
                return 'bg-yellow-100 text-yellow-800';
            case 'cancelled':
                return 'bg-red-100 text-red-800';
            case 'shipped':
                return 'bg-purple-100 text-purple-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    getPaymentStatusClass(order) {
        const status = order.payment_status || 'pending';
        switch (status) {
            case 'paid':
                return 'bg-green-100 text-green-800';
            case 'pending':
                return 'bg-yellow-100 text-yellow-800';
            case 'failed':
                return 'bg-red-100 text-red-800';
            case 'refunded':
                return 'bg-gray-100 text-gray-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    getEmptyStateHTML(type) {
        return `
            <tr>
                <td colspan="9" class="px-6 py-8 text-center text-gray-500">
                    <div class="text-center py-12">
                        <i class="fas fa-shopping-bag text-4xl text-gray-300 mb-4"></i>
                        <p class="text-gray-600 text-lg mb-2">No ${type} found</p>
                        <p class="text-gray-500">Try adjusting your filters or search terms</p>
                    </div>
                </td>
            </tr>
        `;
    }

    updateResultsCount(data) {
        const resultsCount = document.getElementById('results-count');
        if (resultsCount && data.pagination) {
            const start = ((data.pagination.page - 1) * data.pagination.limit) + 1;
            const end = Math.min(data.pagination.page * data.pagination.limit, data.pagination.total);
            resultsCount.textContent = `Showing ${start}-${end} of ${data.pagination.total} orders`;
        }
    }

    renderPagination(pagination) {
        const container = document.getElementById('pagination');
        if (!container || !pagination) return;

        const totalPages = Math.ceil(pagination.total / pagination.limit);
        const currentPage = pagination.page;

        container.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="text-sm text-gray-700">
                    Showing ${((currentPage - 1) * pagination.limit) + 1} to ${Math.min(currentPage * pagination.limit, pagination.total)} of ${pagination.total} orders
                </div>
                <div class="flex space-x-2">
                    ${currentPage > 1 ? `
                        <button onclick="ordersManager.goToPage(${currentPage - 1})" class="px-3 py-1 border rounded hover:bg-gray-50">
                            Previous
                        </button>
                    ` : ''}
                    
                    ${this.generatePaginationButtons(currentPage, totalPages)}
                    
                    ${currentPage < totalPages ? `
                        <button onclick="ordersManager.goToPage(${currentPage + 1})" class="px-3 py-1 border rounded hover:bg-gray-50">
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
                <button onclick="ordersManager.goToPage(${page})" 
                        class="px-3 py-1 border rounded ${page === currentPage ? 'bg-blue-600 text-white' : 'hover:bg-gray-50'}">
                    ${page}
                </button>
            `);
        }

        return buttons.join('');
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadOrders();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Selection functions
    toggleOrderSelection(orderId) {
        const checkbox = document.querySelector(`.order-checkbox[value="${orderId}"]`);
        if (checkbox) {
            if (checkbox.checked) {
                this.selectedOrders.add(orderId);
            } else {
                this.selectedOrders.delete(orderId);
                const selectAll = document.getElementById('select-all-orders');
                if (selectAll) selectAll.checked = false;
            }
            this.updateBulkActions();
        }
    }

    toggleSelectAllOrders() {
        const selectAll = document.getElementById('select-all-orders');
        const checkboxes = document.querySelectorAll('.order-checkbox');

        checkboxes.forEach(checkbox => {
            if (checkbox) {
                checkbox.checked = selectAll.checked;
                if (selectAll.checked) {
                    this.selectedOrders.add(parseInt(checkbox.value));
                } else {
                    this.selectedOrders.delete(parseInt(checkbox.value));
                }
            }
        });

        this.updateBulkActions();
    }

    updateBulkActions() {
        const bulkActions = document.getElementById('bulk-actions');
        if (bulkActions) {
            if (this.selectedOrders.size > 0) {
                bulkActions.style.display = 'flex';
            } else {
                bulkActions.style.display = 'none';
            }
        }
    }

    // Order actions
    async viewOrderDetails(orderId) {
        try {
            const response = await fetch(`/admin-dashboard/api/orders/${orderId}/`);
            if (response.ok) {
                const order = await response.json();
                this.showOrderModal(order);
            } else if (response.status === 404) {
                throw new Error('Order not found');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to load order details');
            }
        } catch (error) {
            console.error('Failed to load order details:', error);
            showToast('Failed to load order details: ' + error.message, 'error');
        }
    }

 
showStatusModal(orderId) {
    console.log('🔧 DEBUG: showStatusModal called with orderId:', orderId);
    
    // Set the current order ID
    this.currentOrderId = orderId;
    console.log('🔧 DEBUG: Current order ID set to:', this.currentOrderId);
    
    const modal = document.getElementById('status-modal');
    if (modal) {
        // Simply remove the hidden class - let Tailwind handle the display
        modal.classList.remove('hidden');
        console.log('🔧 DEBUG: Status modal shown');
    } else {
        console.error('🔧 DEBUG: Status modal element not found');
    }
}





  closeStatusModal() {
    const modal = document.getElementById('status-modal');
    if (modal) {
        // Simply add the hidden class
        modal.classList.add('hidden');
        this.currentOrderId = null;
        console.log('🔧 DEBUG: Status modal closed');
    }
}
    
async confirmStatusUpdate() {
    console.log('🔧 DEBUG: confirmStatusUpdate called');
    console.log('🔧 DEBUG: Current order ID:', this.currentOrderId);
    
    if (!this.currentOrderId) {
        console.error('🔧 DEBUG: No currentOrderId set');
        showToast('No order selected', 'error');
        return;
    }

    const statusSelect = document.getElementById('status-select');
    const statusNotes = document.getElementById('status-notes');
    
    console.log('🔧 DEBUG: Status select element:', statusSelect);
    console.log('🔧 DEBUG: Status notes element:', statusNotes);
    
    if (!statusSelect) {
        console.error('🔧 DEBUG: status-select element not found');
        return;
    }

    const newStatus = statusSelect.value;
    const notes = statusNotes ? statusNotes.value : '';

    console.log('🔧 DEBUG: Updating order', this.currentOrderId, 'to status:', newStatus);
    console.log('🔧 DEBUG: Notes:', notes);

    try {
        const url = `/admin-dashboard/api/orders/update-status/${this.currentOrderId}/`;
        console.log('🔧 DEBUG: Making POST request to:', url);
        
        const csrfToken = getCSRFToken();
        console.log('🔧 DEBUG: CSRF Token available:', !!csrfToken);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                status: newStatus,
                notes: notes
            })
        });
        
        console.log('🔧 DEBUG: Response status:', response.status);
        console.log('🔧 DEBUG: Response OK:', response.ok);
        
        if (response.ok) {
            const result = await response.json();
            console.log('🔧 DEBUG: Success response:', result);
            showToast(result.message || 'Order status updated successfully', 'success');
            this.closeStatusModal();
            this.loadOrders();
            
            // Reset form
            if (statusNotes) statusNotes.value = '';
        } else {
            const errorText = await response.text();
            console.error('🔧 DEBUG: Error response text:', errorText);
            let errorMessage = `Server error: ${response.status}`;
            try {
                const errorData = JSON.parse(errorText);
                errorMessage = errorData.message || errorData.error || errorMessage;
            } catch (e) {
                // Not JSON, use text as is
                errorMessage = errorText || errorMessage;
            }
            throw new Error(errorMessage);
        }
    } catch (error) {
        console.error('🔧 DEBUG: Failed to update order status:', error);
        showToast('Failed to update order status: ' + error.message, 'error');
    }
}

    // Modal functions
    showOrderModal(order) {
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('order-modal-content');

        if (modalTitle) modalTitle.textContent = `Order: ${order.order_number}`;
        if (modalContent) modalContent.innerHTML = this.getOrderModalHTML(order);

        const modal = document.getElementById('order-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    closeOrderModal() {
        const modal = document.getElementById('order-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    getOrderModalHTML(order) {
        return `
            <div class="space-y-6">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                        <h4 class="font-semibold mb-3">Order Information</h4>
                        <div class="space-y-2">
                            <p><strong>Order Number:</strong> ${order.order_number}</p>
                            <p><strong>Customer:</strong> ${order.customer_name || 'N/A'} (${order.customer_email || 'N/A'})</p>
                            <p><strong>Status:</strong> <span class="capitalize">${order.status || 'pending'}</span></p>
                            <p><strong>Payment Status:</strong> <span class="capitalize">${order.payment_status || 'pending'}</span></p>
                            <p><strong>Payment Method:</strong> ${order.payment_method || 'N/A'}</p>
                            <p><strong>Date:</strong> ${new Date(order.created_at).toLocaleString()}</p>
                        </div>
                    </div>
                    <div>
                        <h4 class="font-semibold mb-3">Order Totals</h4>
                        <div class="space-y-2">
                            <p><strong>Subtotal:</strong> $${parseFloat(order.subtotal || 0).toFixed(2)}</p>
                            <p><strong>Shipping:</strong> $${parseFloat(order.shipping_cost || 0).toFixed(2)}</p>
                            <p><strong>Tax:</strong> $${parseFloat(order.tax_amount || 0).toFixed(2)}</p>
                            <p><strong class="text-lg">Grand Total:</strong> $${parseFloat(order.grand_total || 0).toFixed(2)}</p>
                        </div>
                    </div>
                </div>
                
                ${order.shipping_address || order.billing_address ? `
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    ${order.shipping_address ? `
                    <div>
                        <h4 class="font-semibold mb-3">Shipping Address</h4>
                        <div class="bg-gray-50 rounded-lg p-4">
                            <p class="text-sm">${order.shipping_address}</p>
                        </div>
                    </div>
                    ` : ''}
                    ${order.billing_address ? `
                    <div>
                        <h4 class="font-semibold mb-3">Billing Address</h4>
                        <div class="bg-gray-50 rounded-lg p-4">
                            <p class="text-sm">${order.billing_address}</p>
                        </div>
                    </div>
                    ` : ''}
                </div>
                ` : ''}
                
                <div>
                    <h4 class="font-semibold mb-3">Order Items</h4>
                    <div class="border rounded-lg overflow-hidden">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Qty</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                ${order.items && order.items.length > 0 ?
                order.items.map(item => `
                                        <tr>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                ${item.product_name || 'N/A'}
                                            </td>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                $${parseFloat(item.price || 0).toFixed(2)}
                                            </td>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                ${item.quantity || 0}
                                            </td>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                $${parseFloat(item.line_total || 0).toFixed(2)}
                                            </td>
                                        </tr>
                                    `).join('') :
                '<tr><td colspan="4" class="px-6 py-4 text-center text-gray-500">No items found</td></tr>'
            }
                            </tbody>
                        </table>
                    </div>
                </div>

                ${order.status_history && order.status_history.length > 0 ? `
                <div>
                    <h4 class="font-semibold mb-3">Status History</h4>
                    <div class="space-y-2">
                        ${order.status_history.map(history => `
                            <div class="flex items-center justify-between border-b pb-2">
                                <div>
                                    <span class="font-medium capitalize">${history.old_status} → ${history.new_status}</span>
                                    <p class="text-sm text-gray-500">${history.note || 'No notes'}</p>
                                </div>
                                <div class="text-sm text-gray-500">
                                    ${new Date(history.created_at).toLocaleString()}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }

    // Export function
    exportOrders() {
        const queryString = this.buildQueryString().replace('?', '');
        const url = `/admin-dashboard/api/orders/export/${queryString ? '?' + queryString : ''}`;

        // Create a temporary link to trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = 'orders_export.csv';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        showToast('Export started...', 'info');
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
            let displayKey = key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' ');

            // Format display values
            if (key === 'status') {
                displayValue = value.charAt(0).toUpperCase() + value.slice(1);
            } else if (key === 'payment_status') {
                displayValue = value === 'paid' ? 'Paid' :
                    value === 'pending' ? 'Payment Pending' :
                        value.charAt(0).toUpperCase() + value.slice(1);
            }

            return `
                <div class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center">
                    <span>${displayKey}: ${displayValue}</span>
                    <button onclick="ordersManager.removeFilter('${key}')" class="ml-2 text-blue-600 hover:text-blue-800">
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

        // Reset date inputs
        if (filterKey === 'date_from') {
            const dateFrom = document.getElementById('date-from');
            if (dateFrom) dateFrom.value = '';
        }
        if (filterKey === 'date_to') {
            const dateTo = document.getElementById('date-to');
            if (dateTo) dateTo.value = '';
        }

        this.currentPage = 1;
        this.loadOrders();
        this.updateActiveFilters();
    }
}

// Initialize orders manager
let ordersManager;

document.addEventListener('DOMContentLoaded', function () {
    try {
        ordersManager = new OrdersManager();
        console.log('OrdersManager initialized successfully');
    } catch (error) {
        console.error('Failed to initialize OrdersManager:', error);
    }
});

// Global functions
function toggleSelectAllOrders() {
    if (window.ordersManager) {
        window.ordersManager.toggleSelectAllOrders();
    }
}

function closeOrderModal() {
    if (window.ordersManager) {
        window.ordersManager.closeOrderModal();
    } else {
        const modal = document.getElementById('order-modal');
        if (modal) modal.classList.add('hidden');
    }
}


function closeStatusModal() {
    if (window.ordersManager) {
        window.ordersManager.closeStatusModal();
    } else {
        const modal = document.getElementById('status-modal');
        if (modal) modal.classList.add('hidden');
    }
}

function confirmStatusUpdate() {
    if (window.ordersManager) {
        window.ordersManager.confirmStatusUpdate();
    } else {
        console.error('OrdersManager not initialized');
        showToast('System error: Please refresh the page', 'error');
    }
}

function exportOrders() {
    if (window.ordersManager) {
        window.ordersManager.exportOrders();
    }
}

// At the VERY END of admin_orders.js, add this:

// Make functions globally available
window.ordersManager = ordersManager;
window.toggleSelectAllOrders = toggleSelectAllOrders;
window.closeOrderModal = closeOrderModal;
window.closeStatusModal = closeStatusModal;
window.confirmStatusUpdate = confirmStatusUpdate;
window.exportOrders = exportOrders;



document.addEventListener('DOMContentLoaded', function() {
    try {
        ordersManager = new OrdersManager();
        window.ordersManager = ordersManager;
        console.log('✅ OrdersManager initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize OrdersManager:', error);
    }
});