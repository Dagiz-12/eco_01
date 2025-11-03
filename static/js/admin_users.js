// Enhanced Users Management JavaScript
class UsersManager {
    constructor() {
        this.currentPage = 1;
        this.filters = {
            search: '',
            role: '',
            verification: '',
            status: '',
            date_from: '',
            date_to: '',
            sort: 'newest'
        };
        this.selectedUsers = new Set();
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadUsers();
        this.loadUserStats();
    }

    setupEventListeners() {
        // Search input with debounce
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => {
                this.filters.search = searchInput.value;
                this.currentPage = 1;
                this.loadUsers();
            }, 500));
        }

        // Filter changes
        ['role-filter', 'verification-filter', 'status-filter', 'sort-by'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', (e) => {
                    const filterKey = id.replace('-filter', '').replace('-by', '');
                    this.filters[filterKey] = e.target.value;
                    this.currentPage = 1;
                    this.loadUsers();
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
                this.loadUsers();
                this.updateActiveFilters();
            });
        }
        if (dateTo) {
            dateTo.addEventListener('change', (e) => {
                this.filters.date_to = e.target.value;
                this.currentPage = 1;
                this.loadUsers();
                this.updateActiveFilters();
            });
        }

          // Fix: Close modal when clicking the close button or outside
    const userModal = document.getElementById('user-modal');
    const closeButton = userModal ? userModal.querySelector('button[onclick*="closeUserModal"]') : null;
    
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            this.closeUserModal();
        });
    }

    // Close modal when clicking outside
    document.addEventListener('click', (e) => {
        const userModal = document.getElementById('user-modal');
        if (userModal && !userModal.contains(e.target) && !e.target.closest('[onclick*="viewUserDetails"]')) {
            this.closeUserModal();
        }
    });

    // Escape key to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            this.closeUserModal();
        }
    });

    }

    async loadUserStats() {
        try {
            const response = await fetch('/admin-dashboard/api/users/stats/');
            if (response.ok) {
                const stats = await response.json();
                this.updateStatsDisplay(stats);
            }
        } catch (error) {
            console.error('Failed to load user stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        const elements = {
            'total-users': stats.total_users || 0,
            'pending-verification': stats.pending_verification || 0,
            'active-today': stats.active_today || 0,
            'seller-count': stats.seller_count || 0
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }

    async loadUsers() {
        try {
            const queryString = this.buildQueryString();
            const response = await fetch(`/admin-dashboard/api/users/${queryString}`);
            
            if (response.ok) {
                const data = await response.json();
                this.renderUsers(data);
                this.updateResultsCount(data);
            } else {
                throw new Error('Failed to fetch users');
            }
        } catch (error) {
            console.error('Failed to load users:', error);
            showToast('Failed to load users: ' + error.message, 'error');
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

    renderUsers(data) {
        const container = document.getElementById('users-table-body');
        
        if (!data.users || data.users.length === 0) {
            container.innerHTML = this.getEmptyStateHTML('users');
            return;
        }

        container.innerHTML = data.users.map(user => `
            <tr class="hover:bg-gray-50" data-user-id="${user.id}">
                <td class="px-6 py-4 whitespace-nowrap">
                    <input type="checkbox" value="${user.id}" onchange="usersManager.toggleUserSelection(${user.id})" class="user-checkbox">
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                            <span class="text-blue-600 font-semibold text-sm">
                                ${this.getUserInitials(user)}
                            </span>
                        </div>
                        <div>
                            <div class="text-sm font-medium text-gray-900">${user.email}</div>
                            <div class="text-sm text-gray-500">${user.username}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${user.first_name || '-'} ${user.last_name || ''}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${this.getRoleClass(user)}">
                        ${user.role}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${new Date(user.date_joined).toLocaleDateString()}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.email_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                        ${user.email_verified ? 'Verified' : 'Pending'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${user.order_count || 0}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    $${(user.total_spent || 0).toFixed(2)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="usersManager.viewUserDetails(${user.id})" class="text-blue-600 hover:text-blue-900 mr-3">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button onclick="usersManager.toggleUserStatus(${user.id}, ${user.is_active})" class="${user.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'} mr-3">
                        <i class="fas ${user.is_active ? 'fa-user-slash' : 'fa-user-check'}"></i>
                    </button>
                    <button onclick="usersManager.verifyUser(${user.id}, ${user.email_verified})" class="${user.email_verified ? 'text-gray-400' : 'text-green-600 hover:text-green-900'}">
                        <i class="fas ${user.email_verified ? 'fa-check-circle' : 'fa-envelope'}"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        this.renderPagination(data.pagination);
    }

    getRoleClass(user) {
        switch (user.role) {
            case 'admin':
                return 'bg-red-100 text-red-800';
            case 'seller':
                return 'bg-purple-100 text-purple-800';
            case 'customer':
                return 'bg-blue-100 text-blue-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    getUserInitials(user) {
        if (user.first_name && user.last_name) {
            return (user.first_name[0] + user.last_name[0]).toUpperCase();
        }
        return user.email.substring(0, 2).toUpperCase();
    }

    getEmptyStateHTML(type) {
        return `
            <tr>
                <td colspan="10" class="px-6 py-8 text-center text-gray-500">
                    <div class="text-center py-12">
                        <i class="fas fa-users text-4xl text-gray-300 mb-4"></i>
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
            const start = ((data.pagination.page - 1) * data.pagination.page_size) + 1;
            const end = Math.min(data.pagination.page * data.pagination.page_size, data.pagination.total_count);
            resultsCount.textContent = `Showing ${start}-${end} of ${data.pagination.total_count} users`;
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
                    Showing ${((currentPage - 1) * pagination.page_size) + 1} to ${Math.min(currentPage * pagination.page_size, pagination.total_count)} of ${pagination.total_count} users
                </div>
                <div class="flex space-x-2">
                    ${currentPage > 1 ? `
                        <button onclick="usersManager.goToPage(${currentPage - 1})" class="px-3 py-1 border rounded hover:bg-gray-50">
                            Previous
                        </button>
                    ` : ''}
                    
                    ${this.generatePaginationButtons(currentPage, totalPages)}
                    
                    ${currentPage < totalPages ? `
                        <button onclick="usersManager.goToPage(${currentPage + 1})" class="px-3 py-1 border rounded hover:bg-gray-50">
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
                <button onclick="usersManager.goToPage(${page})" 
                        class="px-3 py-1 border rounded ${page === currentPage ? 'bg-blue-600 text-white' : 'hover:bg-gray-50'}">
                    ${page}
                </button>
            `);
        }
        
        return buttons.join('');
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadUsers();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Selection functions
    toggleUserSelection(userId) {
        const checkbox = document.querySelector(`.user-checkbox[value="${userId}"]`);
        if (checkbox.checked) {
            this.selectedUsers.add(userId);
        } else {
            this.selectedUsers.delete(userId);
            const selectAll = document.getElementById('select-all-users');
            if (selectAll) selectAll.checked = false;
        }
        this.updateBulkActions();
    }

    toggleSelectAllUsers() {
        const selectAll = document.getElementById('select-all-users');
        const checkboxes = document.querySelectorAll('.user-checkbox');
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAll.checked;
            if (selectAll.checked) {
                this.selectedUsers.add(parseInt(checkbox.value));
            } else {
                this.selectedUsers.delete(parseInt(checkbox.value));
            }
        });
        
        this.updateBulkActions();
    }

    updateBulkActions() {
        const bulkActions = document.getElementById('bulk-actions');
        if (bulkActions) {
            if (this.selectedUsers.size > 0) {
                bulkActions.style.display = 'flex';
            } else {
                bulkActions.style.display = 'none';
            }
        }
    }

    // User actions
    async viewUserDetails(userId) {
        try {
            const response = await fetch(`/admin-dashboard/api/users/${userId}/`);
            if (response.ok) {
                const user = await response.json();
                this.showUserModal(user);
            }
        } catch (error) {
            console.error('Failed to load user details:', error);
            showToast('Failed to load user details', 'error');
        }
    }

    async toggleUserStatus(userId, isCurrentlyActive) {
        const action = isCurrentlyActive ? 'deactivate' : 'activate';
        
        if (!confirm(`Are you sure you want to ${action} this user?`)) return;
        
        try {
            const response = await fetch(`/admin-dashboard/api/users/${userId}/action/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    action: 'toggle_active'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                showToast(result.message, 'success');
                this.loadUsers();
                this.loadUserStats();
            }
        } catch (error) {
            console.error(`Failed to ${action} user:`, error);
            showToast(`Failed to ${action} user`, 'error');
        }
    }

    async verifyUser(userId, isCurrentlyVerified) {
        if (isCurrentlyVerified) {
            showToast('User is already verified', 'info');
            return;
        }
        
        if (!confirm('Are you sure you want to verify this user?')) return;
        
        try {
            const response = await fetch(`/admin-dashboard/api/users/verify/${userId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                showToast(result.message, 'success');
                this.loadUsers();
                this.loadUserStats();
            }
        } catch (error) {
            console.error('Failed to verify user:', error);
            showToast('Failed to verify user', 'error');
        }
    }

    // Bulk actions
    async bulkVerifyUsers() {
        if (this.selectedUsers.size === 0) return;
        
        if (!confirm(`Verify ${this.selectedUsers.size} user(s)?`)) return;
        
        try {
            const response = await fetch('/admin-dashboard/api/users/bulk-actions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    action: 'verify',
                    user_ids: Array.from(this.selectedUsers)
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                showToast(result.message, 'success');
                this.selectedUsers.clear();
                this.updateBulkActions();
                this.loadUsers();
                this.loadUserStats();
            }
        } catch (error) {
            console.error('Failed to bulk verify users:', error);
            showToast('Failed to verify users', 'error');
        }
    }

    async bulkActivateUsers() {
        if (this.selectedUsers.size === 0) return;
        
        if (!confirm(`Activate ${this.selectedUsers.size} user(s)?`)) return;
        
        try {
            const response = await fetch('/admin-dashboard/api/users/bulk-actions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    action: 'activate',
                    user_ids: Array.from(this.selectedUsers)
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                showToast(result.message, 'success');
                this.selectedUsers.clear();
                this.updateBulkActions();
                this.loadUsers();
                this.loadUserStats();
            }
        } catch (error) {
            console.error('Failed to bulk activate users:', error);
            showToast('Failed to activate users', 'error');
        }
    }

    async bulkDeactivateUsers() {
        if (this.selectedUsers.size === 0) return;
        
        if (!confirm(`Deactivate ${this.selectedUsers.size} user(s)?`)) return;
        
        try {
            const response = await fetch('/admin-dashboard/api/users/bulk-actions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    action: 'deactivate',
                    user_ids: Array.from(this.selectedUsers)
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                showToast(result.message, 'success');
                this.selectedUsers.clear();
                this.updateBulkActions();
                this.loadUsers();
                this.loadUserStats();
            }
        } catch (error) {
            console.error('Failed to bulk deactivate users:', error);
            showToast('Failed to deactivate users', 'error');
        }
    }

    // Export function
    exportUsers() {
        const queryString = this.buildQueryString().replace('?', '');
        const url = `/admin-dashboard/api/users/export/${queryString ? '?' + queryString : ''}`;
        
        // Create a temporary link to trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = 'users_export.csv';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showToast('Export started...', 'info');
    }

    // Modal functions
    showUserModal(user) {
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('user-modal-content');
        
        if (modalTitle) modalTitle.textContent = `User: ${user.email}`;
        if (modalContent) modalContent.innerHTML = this.getUserModalHTML(user);
        
        document.getElementById('user-modal').classList.remove('hidden');
    }

    closeUserModal() {
        document.getElementById('user-modal').classList.add('hidden');
    }

    getUserModalHTML(user) {
        return `
            <div class="space-y-6">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                        <h4 class="font-semibold mb-3">Basic Information</h4>
                        <div class="space-y-2">
                            <p><strong>Email:</strong> ${user.email}</p>
                            <p><strong>Username:</strong> ${user.username}</p>
                            <p><strong>First Name:</strong> ${user.first_name || 'Not set'}</p>
                            <p><strong>Last Name:</strong> ${user.last_name || 'Not set'}</p>
                            <p><strong>Role:</strong> <span class="capitalize">${user.role}</span></p>
                        </div>
                    </div>
                    <div>
                        <h4 class="font-semibold mb-3">Account Status</h4>
                        <div class="space-y-2">
                            <p><strong>Email Verified:</strong> ${user.email_verified ? 'Yes' : 'No'}</p>
                            <p><strong>Account Active:</strong> ${user.is_active ? 'Yes' : 'No'}</p>
                            <p><strong>Date Joined:</strong> ${new Date(user.date_joined).toLocaleString()}</p>
                            <p><strong>Last Login:</strong> ${user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</p>
                        </div>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                        <h4 class="font-semibold mb-3">Order Statistics</h4>
                        <div class="space-y-2">
                            <p><strong>Total Orders:</strong> ${user.order_count || 0}</p>
                            <p><strong>Total Spent:</strong> $${(user.total_spent || 0).toFixed(2)}</p>
                        </div>
                    </div>
                    <div>
                        <h4 class="font-semibold mb-3">Address Information</h4>
                        <div class="space-y-2">
                            ${user.addresses && user.addresses.length > 0 ? 
                                user.addresses.map(address => `
                                    <div class="border rounded p-3">
                                        <p><strong>${address.address_type}:</strong> ${address.street}, ${address.city}, ${address.state} ${address.zip_code}</p>
                                        ${address.is_default ? '<span class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Default</span>' : ''}
                                    </div>
                                `).join('') : 
                                '<p class="text-gray-500">No addresses found</p>'
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;
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
            if (key === 'verification') {
                displayValue = value === 'pending' ? 'Pending Verification' : 'Verified';
            } else if (key === 'status') {
                displayValue = value === 'active' ? 'Active' : 'Inactive';
            } else if (key === 'role') {
                displayValue = value.charAt(0).toUpperCase() + value.slice(1);
            }
            
            return `
                <div class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center">
                    <span>${displayKey}: ${displayValue}</span>
                    <button onclick="usersManager.removeFilter('${key}')" class="ml-2 text-blue-600 hover:text-blue-800">
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
        this.loadUsers();
        this.updateActiveFilters();
    }
}

// Initialize users manager
let usersManager;

document.addEventListener('DOMContentLoaded', function() {
    usersManager = new UsersManager();
});

// Global functions for HTML onclick handlers
function toggleSelectAllUsers() {
    if (window.usersManager) {
        window.usersManager.toggleSelectAllUsers();
    }
}

function bulkVerifyUsers() {
    if (window.usersManager) {
        window.usersManager.bulkVerifyUsers();
    }
}

function bulkActivateUsers() {
    if (window.usersManager) {
        window.usersManager.bulkActivateUsers();
    }
}

function bulkDeactivateUsers() {
    if (window.usersManager) {
        window.usersManager.bulkDeactivateUsers();
    }
}

function exportUsers() {
    if (window.usersManager) {
        window.usersManager.exportUsers();
    }
}

function closeUserModal() {
    if (window.usersManager) {
        window.usersManager.closeUserModal();
    }
}