class HomePageManager {
    constructor() {
        this.loadFeaturedProducts();
        this.loadCategories();
        this.loadTestimonials();
        this.initEventListeners();
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

    async loadFeaturedProducts() {
        const container = document.getElementById('featured-products');
        if (!container) return;

        try {
            const response = await ajaxUtils.makeRequest('/api/home/featured-products/');
            
            if (response.success && response.data.products.length > 0) {
                container.innerHTML = response.data.products.map(product => `
                    <div class="product-card bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
                        <div class="relative">
                            <img src="${product.primary_image || '/static/images/placeholder.jpg'}" 
                                 alt="${product.name}"
                                 class="w-full h-48 object-cover">
                            ${product.is_featured ? `
                                <span class="absolute top-2 right-2 bg-yellow-500 text-white px-2 py-1 rounded text-xs">
                                    <i class="fas fa-star mr-1"></i>Featured
                                </span>
                            ` : ''}
                        </div>
                        <div class="p-4">
                            <h3 class="font-semibold text-lg mb-2 truncate">${product.name}</h3>
                            <p class="text-gray-600 text-sm mb-2">${product.category || ''}</p>
                            <div class="flex items-center justify-between">
                                <span class="text-xl font-bold text-green-600">$${product.price}</span>
                                <button class="add-to-cart-btn bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                                        data-product-id="${product.id}">
                                    <i class="fas fa-cart-plus mr-2"></i>Add to Cart
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
            // If no products from API, keep the static fallback
        } catch (error) {
            console.error('Failed to load featured products:', error);
            // Keep static fallback content
        }
    }

    async loadCategories() {
        const container = document.getElementById('categories-grid');
        if (!container) return;

        try {
            const response = await ajaxUtils.makeRequest('/api/home/categories/');
            
            if (response.success && response.data.categories.length > 0) {
                container.innerHTML = response.data.categories.map(category => `
                    <a href="/products/?category=${category.id}" class="category-card block bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
                        <div class="aspect-w-16 aspect-h-9 bg-gray-200">
                            <img src="${category.image || '/static/images/category-placeholder.jpg'}" 
                                 alt="${category.name}"
                                 class="w-full h-32 object-cover">
                        </div>
                        <div class="p-4 text-center">
                            <h3 class="font-semibold text-lg">${category.name}</h3>
                            <p class="text-gray-600 text-sm">${category.product_count} products</p>
                        </div>
                    </a>
                `).join('');
            }
            // If no categories from API, keep the static fallback
        } catch (error) {
            console.error('Failed to load categories:', error);
            // Keep static fallback content
        }
    }

    async loadTestimonials() {
        const container = document.getElementById('testimonials');
        if (!container) return;

        // Mock testimonials - in real app, these would come from an API
        const testimonials = [
            {
                name: "Sarah M.",
                rating: 5,
                comment: "Amazing products and fast delivery! I've been shopping here for months and always have a great experience.",
                location: "Addis Ababa"
            },
            {
                name: "Michael T.",
                rating: 5,
                comment: "The customer service is exceptional. They helped me resolve an issue within minutes!",
                location: "Dire Dawa"
            },
            {
                name: "Elena K.",
                rating: 5,
                comment: "Great quality products at reasonable prices. Highly recommended for online shopping in Ethiopia.",
                location: "Hawassa"
            }
        ];

        container.innerHTML = testimonials.map(testimonial => `
            <div class="testimonial-card bg-white rounded-lg shadow-md p-6">
                <div class="rating-stars text-yellow-400 text-center mb-4">
                    ${'★'.repeat(testimonial.rating)}${'☆'.repeat(5 - testimonial.rating)}
                </div>
                <p class="text-gray-700 mb-4 text-center">"${testimonial.comment}"</p>
                <div class="text-center">
                    <h4 class="font-semibold">${testimonial.name}</h4>
                    <p class="text-gray-600 text-sm">${testimonial.location}</p>
                </div>
            </div>
        `).join('');
    }

    async subscribeNewsletter(form) {
        const formData = new FormData(form);
        const email = formData.get('email');

        const button = form.querySelector('button[type="submit"]');
        ajaxUtils.showLoading(button, 'Subscribing...');

        try {
            const response = await ajaxUtils.makeRequest('/api/home/newsletter/subscribe/', 'POST', {
                email: email
            });

            if (response.success) {
                ajaxUtils.showMessage(response.data.message || 'Thank you for subscribing to our newsletter!');
                form.reset();
            } else {
                ajaxUtils.showMessage(response.data.errors?.email?.[0] || 'Subscription failed. Please try again.', 'error');
            }
        } catch (error) {
            ajaxUtils.showMessage('Failed to subscribe. Please try again.', 'error');
        } finally {
            ajaxUtils.hideLoading(button);
        }
    }

    async addToCart(button) {
        const productId = button.dataset.productId;

        ajaxUtils.showLoading(button, 'Adding...');

        try {
            const response = await ajaxUtils.makeRequest('/api/cart/add/', 'POST', {
                product_id: productId,
                quantity: 1
            });

            if (response.success) {
                ajaxUtils.showMessage('Product added to cart!');
                // Update cart count if cartManager exists
                if (typeof cartManager !== 'undefined') {
                    cartManager.loadCartCount();
                }
            } else {
                ajaxUtils.showMessage('Failed to add product to cart', 'error');
            }
        } catch (error) {
            ajaxUtils.showMessage('Failed to add product to cart', 'error');
        } finally {
            ajaxUtils.hideLoading(button);
        }
    }
}

// Initialize home page
document.addEventListener('DOMContentLoaded', function() {
    new HomePageManager();
});