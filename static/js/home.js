// static/js/home.js
class HomePageManager {
    constructor() {
        console.log('HomePageManager initialized');
        this.loadFeaturedProducts();
        this.loadCategories();
        this.initEventListeners();
    }

    // static/js/home.js - UPDATE THESE LINES
async loadFeaturedProducts() {
    const container = document.getElementById('featured-products');
    if (!container) {
        console.error('Featured products container not found');
        return;
    }

    try {
        console.log('Loading featured products...');
        // ✅ CORRECT ENDPOINT: /api/home/featured-products/
        const response = await fetch('/api/home/featured-products/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Featured products data:', data);
        
        if (data.success && data.products && data.products.length > 0) {
            container.innerHTML = data.products.map(product => `
                <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
                    <div class="relative">
                        <img src="${product.primary_image || '/static/images/placeholder.jpg'}" 
                             alt="${product.name}"
                             class="w-full h-48 object-cover">
                        ${product.is_featured ? `
                            <span class="absolute top-2 right-2 bg-yellow-500 text-white px-2 py-1 rounded text-xs">
                                Featured
                            </span>
                        ` : ''}
                    </div>
                    <div class="p-4">
                        <h3 class="font-semibold text-lg mb-2">${product.name}</h3>
                        <p class="text-gray-600 text-sm mb-2">${product.category || ''}</p>
                        <div class="flex items-center justify-between">
                            <span class="text-xl font-bold text-green-600">$${product.price}</span>
                            <button class="add-to-cart-btn bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                                    data-product-id="${product.id}">
                                Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
            
            console.log('Featured products loaded successfully');
        } else {
            container.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <p class="text-gray-500">No featured products available.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load featured products:', error);
        container.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-500">Failed to load featured products. Please check console.</p>
            </div>
        `;
    }
}

async loadCategories() {
    const container = document.getElementById('categories-grid');
    if (!container) {
        console.error('Categories grid container not found');
        return;
    }

    try {
        console.log('Loading categories...');
        // ✅ CORRECT ENDPOINT: /api/home/categories/
        const response = await fetch('/api/home/categories/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Categories data:', data);
        
        if (data.success && data.categories && data.categories.length > 0) {
            container.innerHTML = data.categories.map(category => `
                <a href="/products/category/${category.slug}/" class="block bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
                    <img src="${category.image || '/static/images/category-placeholder.jpg'}" 
                         alt="${category.name}"
                         class="w-full h-32 object-cover">
                    <div class="p-4 text-center">
                        <h3 class="font-semibold text-lg">${category.name}</h3>
                        <p class="text-gray-600 text-sm">${category.product_count} products</p>
                    </div>
                </a>
            `).join('');
            
            console.log('Categories loaded successfully');
        } else {
            container.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <p class="text-gray-500">No categories available.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load categories:', error);
        container.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-500">Failed to load categories. Please check console.</p>
            </div>
        `;
    }
}

    initEventListeners() {
        // Newsletter form
        const newsletterForm = document.getElementById('newsletter-form');
        if (newsletterForm) {
            newsletterForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.subscribeNewsletter(e.target);
            });
        }

        // Add to cart buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.add-to-cart-btn')) {
                this.addToCart(e.target.closest('.add-to-cart-btn'));
            }
        });
    }

    async subscribeNewsletter(form) {
        const formData = new FormData(form);
        const email = formData.get('email');

        try {
            const response = await fetch('/api/home/newsletter/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ email: email })
            });

            const data = await response.json();
            
            if (data.success) {
                alert('Thank you for subscribing!');
                form.reset();
            } else {
                alert('Subscription failed: ' + (data.errors?.email?.[0] || 'Unknown error'));
            }
        } catch (error) {
            console.error('Newsletter subscription error:', error);
            alert('Subscription failed. Please try again.');
        }
    }

    async addToCart(button) {
        const productId = button.dataset.productId;
        console.log('Adding to cart:', productId);

        // Simple cart functionality for now
        alert(`Product ${productId} added to cart!`);
        
        // You can implement actual cart API call here later
        // await fetch('/api/cart/add/', {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json',
        //         'X-CSRFToken': this.getCSRFToken()
        //     },
        //     body: JSON.stringify({
        //         product_id: productId,
        //         quantity: 1
        //     })
        // });
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
}

// Initialize home page
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing HomePageManager...');
    new HomePageManager();
});