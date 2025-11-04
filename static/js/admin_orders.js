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
        
        // Emergency: Ensure global access
        setTimeout(() => {
            window.ordersManager = this;
            console.log('✅ Emergency global access set');
        }, 100);
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


         // Add this for the detailed payment status filter
    const paymentStatusDetailedFilter = document.getElementById('payment-status-detailed-filter');
    if (paymentStatusDetailedFilter) {
        paymentStatusDetailedFilter.addEventListener('change', (e) => {
            this.filters.payment_status_detailed = e.target.value;
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
            case 'delivered':
                return 'bg-green-100 text-green-800';
            case 'processing':
                return 'bg-blue-100 text-blue-800';
            case 'pending':
                return 'bg-yellow-100 text-yellow-800';
            case 'cancelled':
                return 'bg-red-100 text-red-800';
            case 'shipped':
                return 'bg-purple-100 text-purple-800';
            case 'confirmed':
                return 'bg-indigo-100 text-indigo-800';
            case 'refunded':
                return 'bg-gray-100 text-gray-800';
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
            // Handle order not found gracefully - might be updating
            console.warn(`Order ${orderId} not found - might be updating, will retry...`);
            
            // Retry after a short delay
            setTimeout(async () => {
                try {
                    const retryResponse = await fetch(`/admin-dashboard/api/orders/${orderId}/`);
                    if (retryResponse.ok) {
                        const order = await retryResponse.json();
                        this.showOrderModal(order);
                    } else {
                        showToast('Order details temporarily unavailable. Please refresh the page.', 'warning');
                    }
                } catch (retryError) {
                    console.error('Retry failed:', retryError);
                }
            }, 1000);
            
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to load order details');
        }
    } catch (error) {
        console.error('Failed to load order details:', error);
        // Don't show error for temporary "Order not found" during updates
        if (!error.message.includes('Order not found') && !error.message.includes('404')) {
            showToast('Failed to load order details: ' + error.message, 'error');
        }
    }
}
// In your status modal, add payment status display
showStatusModal(orderId) {
    console.log('🔧 DEBUG: showStatusModal called with orderId:', orderId);
    
    this.currentOrderId = orderId;
    
    const modal = document.getElementById('status-modal');
    if (modal) {
        modal.classList.remove('hidden');
        
        // Load payment status and add warning
        this.loadOrderPaymentStatus(orderId).then(paymentStatus => {
            this.addPaymentStatusWarning(paymentStatus);
        }).catch(error => {
            console.error('Failed to load payment status:', error);
        });
    }
}

async loadOrderPaymentStatus(orderId) {
    try {
        const response = await fetch(`/admin-dashboard/api/orders/${orderId}/`);
        const orderData = await response.json();
        return orderData.payment_status;
    } catch (error) {
        console.error('Failed to load payment status:', error);
        return 'unknown';
    }
}

addPaymentStatusWarning(paymentStatus) {
    console.log('🔧 Adding payment warning for status:', paymentStatus);
    
    const statusSelect = document.getElementById('status-select');
    if (!statusSelect) {
        console.error('❌ Status select not found');
        return;
    }
    
    const statusContainer = statusSelect.parentElement;
    if (!statusContainer) {
        console.error('❌ Status container not found');
        return;
    }
    
    // Remove existing warning
    const existingWarning = document.getElementById('payment-warning');
    if (existingWarning) {
        existingWarning.remove();
    }
    
    // Add warning if payment not received
    if (paymentStatus !== 'paid') {
        const warning = document.createElement('div');
        warning.id = 'payment-warning';
        warning.className = 'bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4';
        warning.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-triangle text-yellow-600 mr-3"></i>
                <div>
                    <p class="text-yellow-800 font-medium">Payment Required</p>
                    <p class="text-yellow-700 text-sm">
                        Order cannot be confirmed until payment is received. 
                        Current payment status: <strong>${paymentStatus}</strong>
                    </p>
                </div>
            </div>
        `;
        
        // SAFE INSERTION: Insert before the container
        statusContainer.parentElement.insertBefore(warning, statusContainer);
        
        // Disable confirmed option
        const confirmedOption = statusSelect.querySelector('option[value="confirmed"]');
        if (confirmedOption) {
            confirmedOption.disabled = true;
            confirmedOption.title = 'Payment required before confirmation';
        }
    } else {
        // Enable confirmed option if paid
        const confirmedOption = statusSelect.querySelector('option[value="confirmed"]');
        if (confirmedOption) {
            confirmedOption.disabled = false;
            confirmedOption.title = '';
        }
    }
}

closeStatusModal() {
    const modal = document.getElementById('status-modal');
    if (modal) {
        // Simply add the hidden class
        modal.classList.add('hidden');
        
        // RESET THE FORM FIELDS
        const statusSelect = document.getElementById('status-select');
        const statusNotes = document.getElementById('status-notes');
        
        if (statusSelect) {
            statusSelect.value = 'pending'; // Reset to default value
        }
        
        if (statusNotes) {
            statusNotes.value = ''; // Clear the notes
        }
        
        this.currentOrderId = null;
        console.log('🔧 DEBUG: Status modal closed and form reset');
    }
}
    
async confirmStatusUpdate() {
    console.log('🔧 DEBUG: confirmStatusUpdate called');
    
    if (!this.currentOrderId) {
        showToast('No order selected', 'error');
        return;
    }

    const statusSelect = document.getElementById('status-select');
    const statusNotes = document.getElementById('status-notes');
    
    const newStatus = statusSelect.value;
    const notes = statusNotes ? statusNotes.value : '';

    // 🚨 PAYMENT VALIDATION: Prevent confirming unpaid orders
    if (newStatus === 'confirmed') {
        try {
            // Get order details
            const orderResponse = await fetch(`/admin-dashboard/api/orders/${this.currentOrderId}/`);
            const orderData = await orderResponse.json();
            
            // Get payments separately
            const paymentsResponse = await fetch(`/admin-dashboard/api/orders/${this.currentOrderId}/payments/`);
            const paymentsData = await paymentsResponse.json();
            
            // Check payment requirements
            const isPaid = orderData.payment_status === 'paid';
            const hasPayment = paymentsData.success && paymentsData.payments.length > 0;
            const paymentCompleted = hasPayment && paymentsData.payments[0].status === 'completed';
            
            console.log('🔍 Payment Validation:', {
                isPaid,
                hasPayment,
                paymentCompleted,
                orderPaymentStatus: orderData.payment_status,
                paymentData: paymentsData
            });
            
            if (!isPaid || !hasPayment || !paymentCompleted) {
                let errorMessage = 'Cannot confirm order: ';
                if (!isPaid) errorMessage += 'Payment not received. ';
                if (!hasPayment) errorMessage += 'No payment record found. ';
                if (!paymentCompleted) errorMessage += 'Payment not completed.';
                
                showToast(errorMessage, 'error');
                return;
            }
            
        } catch (error) {
            console.error('❌ Failed to validate payment:', error);
            showToast('Error validating payment status', 'error');
            return;
        }
    }

    // Continue with status update if validation passes
    console.log('🔧 DEBUG: Payment validation passed, updating status...');
    
    try {
        const url = `/admin-dashboard/api/orders/update-status/${this.currentOrderId}/`;
        const csrfToken = getCSRFToken();
        
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
        
        if (response.ok) {
            const result = await response.json();
            showToast(result.message || 'Order status updated successfully', 'success');
            
            // Close modal first
            this.closeStatusModal();
            
            // 🔄 CRITICAL: Refresh orders table after successful update
            setTimeout(() => {
                this.loadOrders();
            }, 500);
            
        } else {
            const errorText = await response.text();
            let errorMessage = `Server error: ${response.status}`;
            try {
                const errorData = JSON.parse(errorText);
                errorMessage = errorData.message || errorData.error || errorMessage;
            } catch (e) {
                // Not JSON, use text as is
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
    // Get payment information if available
    const payment = order.payment || {};
    const payments = order.payments || [];
    const primaryPayment = payments.length > 0 ? payments[0] : null;

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
            
            <!-- PAYMENT INFORMATION SECTION -->
            <div class="border-t pt-6">
                <h4 class="font-semibold mb-3">Payment Information</h4>
                ${primaryPayment ? `
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 bg-gray-50 rounded-lg p-4">
                        <div>
                            <p><strong>Payment ID:</strong> ${primaryPayment.payment_id || 'N/A'}</p>
                            <p><strong>Payment Method:</strong> <span class="capitalize">${primaryPayment.payment_method || 'N/A'}</span></p>
                            <p><strong>Amount:</strong> $${parseFloat(primaryPayment.amount || 0).toFixed(2)} ${primaryPayment.currency || 'ETB'}</p>
                        </div>
                        <div>
                            <p><strong>Payment Status:</strong> 
                                <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${this.getPaymentStatusClass(primaryPayment)}">
                                    ${primaryPayment.status || 'pending'}
                                </span>
                            </p>
                            <p><strong>Gateway ID:</strong> ${primaryPayment.gateway_payment_id || 'N/A'}</p>
                            <p><strong>Paid At:</strong> ${primaryPayment.completed_at ? new Date(primaryPayment.completed_at).toLocaleString() : 'Not completed'}</p>
                        </div>
                    </div>
                    
                    <!-- PAYMENT ACTIONS -->
                    <div class="mt-4 flex space-x-3">
                        ${primaryPayment.status === 'pending' || primaryPayment.status === 'processing' ? `
                            <button onclick="ordersManager.verifyPayment(${order.id}, ${primaryPayment.id})" 
                                    class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                                <i class="fas fa-check-circle mr-2"></i>Verify Payment
                            </button>
                        ` : ''}
                        
                        ${primaryPayment.status === 'completed' ? `
                            <button onclick="ordersManager.initiateRefund(${order.id}, ${primaryPayment.id})" 
                                    class="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors">
                                <i class="fas fa-undo mr-2"></i>Initiate Refund
                            </button>
                        ` : ''}
                        
                        <button onclick="ordersManager.viewPaymentDetails(${order.id})" 
                                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                            <i class="fas fa-credit-card mr-2"></i>Payment Details
                        </button>
                    </div>
                ` : `
                    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <div class="flex items-center">
                            <i class="fas fa-exclamation-triangle text-yellow-600 mr-3"></i>
                            <div>
                                <p class="text-yellow-800 font-medium">No payment information found</p>
                                <p class="text-yellow-700 text-sm">This order doesn't have an associated payment record.</p>
                            </div>
                        </div>
                    </div>
                `}
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
        let displayKey = key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ');

        // Format display values
        if (key === 'status') {
            displayValue = value.charAt(0).toUpperCase() + value.slice(1);
        } else if (key === 'payment_status') {
            displayValue = value === 'paid' ? 'Paid' :
                value === 'pending' ? 'Payment Pending' :
                value.charAt(0).toUpperCase() + value.slice(1);
        } else if (key === 'payment_status_detailed') {
            const statusMap = {
                'completed': 'Paid',
                'processing': 'Processing',
                'pending': 'Pending',
                'failed': 'Failed',
                'refunded': 'Refunded',
                'no_payment': 'No Payment'
            };
            displayValue = statusMap[value] || value;
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

    // Add these methods to your OrdersManager class

// Payment status class helper (if not already exists)
getPaymentStatusClass(payment) {
    const status = payment.status || 'pending';
    switch (status) {
        case 'completed':
            return 'bg-green-100 text-green-800';
        case 'processing':
            return 'bg-blue-100 text-blue-800';
        case 'pending':
            return 'bg-yellow-100 text-yellow-800';
        case 'failed':
            return 'bg-red-100 text-red-800';
        case 'refunded':
            return 'bg-gray-100 text-gray-800';
        case 'partially_refunded':
            return 'bg-orange-100 text-orange-800';
        case 'cancelled':
            return 'bg-red-100 text-red-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

// Payment verification method
async verifyPayment(orderId, paymentId) {
    try {
        console.log('🔧 DEBUG: Verifying payment', paymentId, 'for order', orderId);
        
        const response = await fetch(`/admin-dashboard/api/payments/${paymentId}/verify/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('🔧 DEBUG: Payment verification result:', result);
            showToast(result.message || 'Payment verified successfully', 'success');
            
            // 🔄 CRITICAL: Refresh the orders table to show updated status
            setTimeout(() => {
                this.loadOrders();
            }, 500);
            
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Payment verification failed');
        }
    } catch (error) {
        console.error('🔧 DEBUG: Failed to verify payment:', error);
        showToast('Failed to verify payment: ' + error.message, 'error');
    }
}

// Refund initiation method
async initiateRefund(orderId, paymentId) {
    console.log('🔧 DEBUG: Initiating refund for payment', paymentId);
    
    // For now, show a placeholder - we'll implement the refund modal later
    showToast('Refund functionality will be implemented in the next phase', 'info');
    
    // You can implement a refund modal similar to the status update modal
    // this.showRefundModal(orderId, paymentId);
}

// View payment details method
// In your viewPaymentDetails method or any other payment actions
async viewPaymentDetails(orderId) {
    try {
        const response = await fetch(`/admin-dashboard/api/orders/${orderId}/payments/`);
        if (response.ok) {
            const data = await response.json();
            
            if (data.success && data.payments.length > 0) {
                this.showPaymentDetailsModal(data.payments[0]);
            } else {
                showToast('No payment details found for this order', 'warning');
            }
        } else {
            throw new Error('Failed to fetch payment details');
        }
    } catch (error) {
        console.error('🔧 DEBUG: Failed to fetch payment details:', error);
        showToast('Failed to load payment details: ' + error.message, 'error');
    }
}

showPaymentDetailsModal(payment) {
    const modalContent = `
        <div class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <h5 class="font-semibold mb-2">Payment Information</h5>
                    <div class="space-y-1 text-sm">
                        <p><strong>Payment ID:</strong> ${payment.payment_id}</p>
                        <p><strong>Method:</strong> ${payment.payment_method}</p>
                        <p><strong>Status:</strong> 
                            <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${this.getPaymentStatusClass(payment)}">
                                ${payment.status}
                            </span>
                        </p>
                        <p><strong>Amount:</strong> ${payment.amount} ${payment.currency}</p>
                    </div>
                </div>
                <div>
                    <h5 class="font-semibold mb-2">Gateway Information</h5>
                    <div class="space-y-1 text-sm">
                        <p><strong>Gateway ID:</strong> ${payment.gateway_payment_id || 'N/A'}</p>
                        <p><strong>Created:</strong> ${new Date(payment.created_at).toLocaleString()}</p>
                        <p><strong>Completed:</strong> ${payment.completed_at ? new Date(payment.completed_at).toLocaleString() : 'Not completed'}</p>
                    </div>
                </div>
            </div>
            
            ${payment.gateway_details ? `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h5 class="font-semibold mb-2 text-blue-800">Gateway Details</h5>
                <div class="space-y-1 text-sm text-blue-700">
                    <p><strong>Type:</strong> ${payment.gateway_details.type}</p>
                    <p><strong>Transaction ID:</strong> ${payment.gateway_details.transaction_id}</p>
                    ${payment.gateway_details.ussd_code ? `
                        <p><strong>USSD Code:</strong> <code class="bg-blue-100 px-2 py-1 rounded">${payment.gateway_details.ussd_code}</code></p>
                    ` : ''}
                    ${payment.gateway_details.qr_code_url ? `
                        <p><strong>QR Code:</strong> <a href="${payment.gateway_details.qr_code_url}" target="_blank" class="text-blue-600 underline">View QR Code</a></p>
                    ` : ''}
                </div>
            </div>
            ` : ''}
            
            <div class="flex justify-end space-x-3 pt-4 border-t">
                <button type="button" onclick="closePaymentDetailsModal()" 
                        class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                    Close
                </button>
                ${payment.status === 'pending' || payment.status === 'processing' ? `
                    <button type="button" onclick="ordersManager.verifyPayment(${payment.order_id || 'null'}, ${payment.id})" 
                            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                        <i class="fas fa-check-circle mr-2"></i>Verify Payment
                    </button>
                ` : ''}
            </div>
        </div>
    `;
    
    // Create or update payment details modal
    let modal = document.getElementById('payment-details-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'payment-details-modal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 hidden z-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg w-full max-w-2xl max-h-[80vh] overflow-y-auto">
                <div class="p-6 border-b">
                    <div class="flex justify-between items-center">
                        <h3 class="text-xl font-semibold">Payment Details</h3>
                        <button type="button" onclick="closePaymentDetailsModal()" class="text-gray-500 hover:text-gray-700">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                </div>
                <div class="p-6" id="payment-details-content">
                    ${modalContent}
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    } else {
        document.getElementById('payment-details-content').innerHTML = modalContent;
    }
    
    modal.classList.remove('hidden');
}


// Add to your OrdersManager class

getDetailedPaymentStatusClass(order) {
    const status = order.payment_status_detailed || 'no_payment';
    switch (status) {
        case 'completed':
            return 'bg-green-100 text-green-800';
        case 'processing':
            return 'bg-blue-100 text-blue-800';
        case 'pending':
            return 'bg-yellow-100 text-yellow-800';
        case 'failed':
            return 'bg-red-100 text-red-800';
        case 'refunded':
            return 'bg-gray-100 text-gray-800';
        case 'partially_refunded':
            return 'bg-orange-100 text-orange-800';
        case 'no_payment':
            return 'bg-gray-100 text-gray-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

getDetailedPaymentStatusText(order) {
    const status = order.payment_status_detailed || 'no_payment';
    const statusMap = {
        'completed': 'Paid',
        'processing': 'Processing',
        'pending': 'Pending',
        'failed': 'Failed',
        'refunded': 'Refunded',
        'partially_refunded': 'Partial Refund',
        'no_payment': 'No Payment'
    };
    return statusMap[status] || status;
}

// Update your renderOrders method to include payment status column
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
                <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${this.getDetailedPaymentStatusClass(order)}">
                    ${this.getDetailedPaymentStatusText(order)}
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
                <button onclick="ordersManager.showStatusModal(${order.id})" class="text-green-600 hover:text-green-900 mr-3" title="Update Status">
                    <i class="fas fa-edit"></i>
                </button>
                ${order.has_payment ? `
                    <button onclick="ordersManager.viewPaymentDetails(${order.id})" class="text-purple-600 hover:text-purple-900" title="Payment Details">
                        <i class="fas fa-credit-card"></i>
                    </button>
                ` : `
                    <span class="text-gray-400 cursor-not-allowed" title="No Payment">
                        <i class="fas fa-credit-card"></i>
                    </span>
                `}
            </td>
        </tr>
    `).join('');

    this.renderPagination(data.pagination);
}

}


function closePaymentDetailsModal() {
    const modal = document.getElementById('payment-details-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}


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

// Make manager globally available and initialize
let ordersManager;

document.addEventListener('DOMContentLoaded', function() {
    try {
        ordersManager = new OrdersManager();
        window.ordersManager = ordersManager;
        console.log('✅ OrdersManager initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize OrdersManager:', error);
    }
});