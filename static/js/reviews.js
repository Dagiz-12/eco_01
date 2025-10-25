class ReviewsManager {
    constructor() {
        this.currentProductId = null;
        this.currentPage = 1;
        this.initEventListeners();
    }

    initEventListeners() {
        // Review form submission
        document.addEventListener('submit', (e) => {
            if (e.target.id === 'review-form') {
                e.preventDefault();
                this.submitReview(e.target);
            }
        });

        // Review filtering
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('review-filter')) {
                this.filterReviews();
            }
        });

        // Helpful votes
        document.addEventListener('click', (e) => {
            if (e.target.closest('.helpful-vote-btn')) {
                this.submitVote(e.target.closest('.helpful-vote-btn'));
            }
        });

        // Review image modals
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('review-image-thumbnail')) {
                this.openImageModal(e.target);
            }
        });
    }

    async submitReview(form) {
        const formData = new FormData(form);
        const productId = formData.get('product_id');
        const rating = formData.get('rating');
        const title = formData.get('title');
        const comment = formData.get('comment');

        // Validate rating
        if (!rating) {
            ajaxUtils.showMessage('Please select a rating', 'error');
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        ajaxUtils.showLoading(submitBtn, 'Submitting...');

        const response = await ajaxUtils.makeRequest('/api/reviews/create/', 'POST', {
            product: productId,
            rating: parseInt(rating),
            title: title,
            comment: comment
        });

        if (response.success) {
            ajaxUtils.showMessage('Review submitted successfully! It will be visible after approval.');
            form.reset();
            this.resetStarRating();
            this.loadReviews(productId);
        } else {
            const errors = response.error;
            if (typeof errors === 'object') {
                Object.values(errors).forEach(error => {
                    ajaxUtils.showMessage(error[0], 'error');
                });
            } else {
                ajaxUtils.showMessage('Failed to submit review', 'error');
            }
        }

        ajaxUtils.hideLoading(submitBtn);
    }

    resetStarRating() {
        const stars = document.querySelectorAll('.star-rating input');
        stars.forEach(star => {
            star.checked = false;
        });
        
        const starLabels = document.querySelectorAll('.star-rating label');
        starLabels.forEach(label => {
            label.classList.remove('text-yellow-400');
            label.classList.add('text-gray-300');
        });
    }

    initStarRating() {
        const starRatings = document.querySelectorAll('.star-rating');
        
        starRatings.forEach(rating => {
            const inputs = rating.querySelectorAll('input');
            const labels = rating.querySelectorAll('label');
            
            inputs.forEach((input, index) => {
                input.addEventListener('change', () => {
                    // Update star colors
                    labels.forEach((label, labelIndex) => {
                        if (labelIndex <= index) {
                            label.classList.remove('text-gray-300');
                            label.classList.add('text-yellow-400');
                        } else {
                            label.classList.remove('text-yellow-400');
                            label.classList.add('text-gray-300');
                        }
                    });
                });
            });
        });
    }

    async loadReviews(productId, page = 1) {
        this.currentProductId = productId;
        this.currentPage = page;

        const container = document.getElementById('reviews-container');
        if (!container) return;

        const filters = this.getActiveFilters();
        const params = new URLSearchParams({
            product: productId,
            page: page,
            ...filters
        });

        const response = await ajaxUtils.makeRequest(`/api/reviews/?${params}`);

        if (response.success) {
            this.renderReviews(container, response.data);
            this.updateReviewStats(response.data.stats);
        } else {
            ajaxUtils.showMessage('Failed to load reviews', 'error');
        }
    }

    renderReviews(container, data) {
        const reviews = data.results || [];
        
        if (reviews.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-comment-slash text-4xl text-gray-300 mb-4"></i>
                    <h3 class="text-lg font-semibold text-gray-600">No reviews yet</h3>
                    <p class="text-gray-500">Be the first to review this product!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = reviews.map(review => `
            <div class="review-item bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h4 class="font-semibold text-lg">${review.title}</h4>
                        <div class="flex items-center space-x-2 mt-1">
                            <div class="rating-stars text-yellow-400">
                                ${this.renderStarRating(review.rating)}
                            </div>
                            <span class="text-sm text-gray-500">by ${review.user.first_name || review.user.email}</span>
                            ${review.is_verified_purchase ? `
                                <span class="verified-badge bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                                    <i class="fas fa-check-circle mr-1"></i>Verified Purchase
                                </span>
                            ` : ''}
                        </div>
                    </div>
                    <span class="text-sm text-gray-500">${this.formatDate(review.created_at)}</span>
                </div>

                <p class="text-gray-700 mb-4">${review.comment}</p>

                ${review.images && review.images.length > 0 ? `
                    <div class="review-images flex space-x-2 mb-4">
                        ${review.images.map(image => `
                            <img src="${image.image}" 
                                 alt="${image.alt_text || 'Review image'}"
                                 class="review-image-thumbnail w-16 h-16 object-cover rounded cursor-pointer border border-gray-200 hover:border-blue-500">
                        `).join('')}
                    </div>
                ` : ''}

                <div class="flex justify-between items-center">
                    <button class="helpful-vote-btn flex items-center space-x-1 text-sm text-gray-600 hover:text-blue-600"
                            data-review-id="${review.id}"
                            data-voted="${review.user_has_voted}">
                        <i class="fas fa-thumbs-up ${review.user_has_voted ? 'text-blue-600' : ''}"></i>
                        <span>Helpful (${review.helpful_votes})</span>
                    </button>

                    ${review.user_has_voted && review.user_vote_type ? `
                        <span class="text-xs text-gray-500">
                            You marked this as ${review.user_vote_type}
                        </span>
                    ` : ''}
                </div>
            </div>
        `).join('');

        // Update pagination
        this.updatePagination(data.pagination);
    }

    renderStarRating(rating) {
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= rating) {
                stars += '<i class="fas fa-star"></i>';
            } else {
                stars += '<i class="far fa-star"></i>';
            }
        }
        return stars;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    async submitVote(button) {
        const reviewId = button.dataset.reviewId;
        const hasVoted = button.dataset.voted === 'true';
        const voteType = hasVoted ? 'not_helpful' : 'helpful';

        if (hasVoted) {
            // Can't change vote in this simple implementation
            ajaxUtils.showMessage('You have already voted on this review', 'info');
            return;
        }

        const response = await ajaxUtils.makeRequest(`/api/reviews/${reviewId}/vote/`, 'POST', {
            vote_type: voteType
        });

        if (response.success) {
            ajaxUtils.showMessage('Thank you for your feedback!');
            
            // Update button state
            button.dataset.voted = 'true';
            button.querySelector('i').classList.add('text-blue-600');
            
            // Update vote count
            const voteText = button.querySelector('span');
            const currentCount = parseInt(voteText.textContent.match(/\d+/)[0]);
            voteText.textContent = `Helpful (${currentCount + 1})`;
        } else {
            ajaxUtils.showMessage('Failed to submit vote', 'error');
        }
    }

    getActiveFilters() {
        const filters = {};
        const ratingFilter = document.querySelector('input[name="rating_filter"]:checked');
        const sortFilter = document.querySelector('select[name="sort_reviews"]');

        if (ratingFilter && ratingFilter.value) {
            filters.rating = ratingFilter.value;
        }

        if (sortFilter && sortFilter.value) {
            filters.ordering = sortFilter.value;
        }

        return filters;
    }

    filterReviews() {
        if (this.currentProductId) {
            this.loadReviews(this.currentProductId, 1);
        }
    }

    updateReviewStats(stats) {
        if (!stats) return;

        // Update rating distribution
        this.updateRatingDistribution(stats.rating_distribution);
        
        // Update average rating
        const avgRatingEl = document.getElementById('average-rating');
        if (avgRatingEl) {
            avgRatingEl.textContent = stats.average_rating.toFixed(1);
        }

        // Update total reviews
        const totalReviewsEl = document.getElementById('total-reviews');
        if (totalReviewsEl) {
            totalReviewsEl.textContent = stats.total_reviews;
        }
    }

    updateRatingDistribution(distribution) {
        const container = document.getElementById('rating-distribution');
        if (!container) return;

        container.innerHTML = '';
        
        for (let rating = 5; rating >= 1; rating--) {
            const percentage = distribution[rating] || 0;
            const bar = `
                <div class="rating-bar flex items-center space-x-2 mb-2">
                    <span class="text-sm text-gray-600 w-8">${rating}★</span>
                    <div class="flex-1 bg-gray-200 rounded-full h-2">
                        <div class="bg-yellow-400 h-2 rounded-full" 
                             style="width: ${percentage}%"></div>
                    </div>
                    <span class="text-sm text-gray-600 w-12">${percentage}%</span>
                </div>
            `;
            container.innerHTML += bar;
        }
    }

    updatePagination(pagination) {
        const container = document.getElementById('reviews-pagination');
        if (!container || !pagination) return;

        const { current_page, total_pages, has_next, has_previous } = pagination;

        container.innerHTML = `
            <div class="flex justify-center items-center space-x-2">
                <button class="pagination-btn ${!has_previous ? 'opacity-50 cursor-not-allowed' : ''}"
                        ${has_previous ? `onclick="reviewsManager.loadReviews('${this.currentProductId}', ${current_page - 1})"` : 'disabled'}>
                    <i class="fas fa-chevron-left"></i> Previous
                </button>
                
                <span class="px-4 py-2 text-sm text-gray-600">
                    Page ${current_page} of ${total_pages}
                </span>
                
                <button class="pagination-btn ${!has_next ? 'opacity-50 cursor-not-allowed' : ''}"
                        ${has_next ? `onclick="reviewsManager.loadReviews('${this.currentProductId}', ${current_page + 1})"` : 'disabled'}>
                    Next <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
    }

    openImageModal(image) {
        const modal = document.getElementById('review-image-modal');
        const modalImage = document.getElementById('modal-review-image');
        
        if (modal && modalImage) {
            modalImage.src = image.src;
            modal.classList.remove('hidden');
        }
    }

    closeImageModal() {
        const modal = document.getElementById('review-image-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
}

// Global instance
const reviewsManager = new ReviewsManager();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    reviewsManager.initStarRating();
});