class ProfileManager {
    constructor() {
        this.init();
    }

    async init() {
        await this.loadProfileData();
        await this.loadAddresses();
    }

    async loadProfileData() {
        try {
            const response = await fetch('/api/users/api/profile/');
            if (response.ok) {
                const userData = await response.json();
                this.renderProfile(userData);
            }
        } catch (error) {
            console.error('Failed to load profile:', error);
        }
    }

    renderProfile(userData) {
        const container = document.getElementById('profile-info');
        if (!container) return;

        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">Email</label>
                    <p class="mt-1 text-gray-900">${userData.email || 'N/A'}</p>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Username</label>
                    <p class="mt-1 text-gray-900">${userData.username || 'N/A'}</p>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Phone</label>
                    <p class="mt-1 text-gray-900">${userData.phone || 'N/A'}</p>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Role</label>
                    <p class="mt-1 text-gray-900 capitalize">${userData.role || 'customer'}</p>
                </div>
            </div>
        `;
    }

    async loadAddresses() {
        try {
            const response = await fetch('/api/users/api/profile/');
            if (response.ok) {
                const userData = await response.json();
                this.renderAddresses(userData.addresses || []);
            }
        } catch (error) {
            console.error('Failed to load addresses:', error);
        }
    }

    renderAddresses(addresses) {
        const container = document.getElementById('addresses-list');
        if (!container) return;

        if (addresses.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-map-marker-alt text-4xl text-gray-300 mb-4"></i>
                    <p class="text-gray-600">No addresses saved yet</p>
                </div>
            `;
            return;
        }

        container.innerHTML = addresses.map(address => `
            <div class="border rounded-lg p-4 mb-4">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center mb-2">
                            <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded capitalize">
                                ${address.address_type}
                            </span>
                            ${address.is_default ? 
                                '<span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded ml-2">Default</span>' : 
                                ''
                            }
                        </div>
                        <p class="font-semibold">${address.street}</p>
                        <p class="text-gray-600">${address.city}, ${address.state} ${address.zip_code}</p>
                        <p class="text-gray-600">${address.country}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="text-red-600 hover:text-red-800">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

// Initialize profile manager
document.addEventListener('DOMContentLoaded', function() {
    new ProfileManager();
});