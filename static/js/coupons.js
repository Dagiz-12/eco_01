class CouponManager {
    constructor() {
        this.initEventListeners();
        this.loadAvailableCoupons();
    }

    initEventListeners() {
        // Apply coupon form
        document.addEventListener('submit', (e) => {
            if (e.target.id === 'apply-coupon-form') {
                e.preventDefault();
                this.applyCoupon(e.target);
            }
        });

        // Remove coupon
        document.addEventListener('click', (e) => {
            if (e.target.closest('.remove-coupon-btn')) {
                this.removeCoupon();
            }
        });

        // Copy coupon code
        document.addEventListener('click', (e) => {
            if (e.target.closest('.copy-coupon-btn')) {
                this.copyCouponCode(e.target.closest('.copy-coupon-btn'));
            }
        });
    }

    async applyCoupon(form) {
        const formData = new FormData(form);
        const code = formData.get('coupon_code');
        const orderAmount = form.dataset.orderAmount || 0;

        const submitBtn = form.querySelector('button[type="submit"]');
        ajaxUtils.showLoading(submitBtn, 'Applying...');

        const response = await ajaxUtils.makeRequest('/api/coupons/validate/', 'POST', {
            code: code,
            order_amount: parseFloat(orderAmount)
        });

        if (response.success && response.data.valid) {
            ajaxUtils.showMessage(response.data.message);
            this.displayAppliedCoupon(response.data);
            
            // Update order totals
            this.updateOrderTotals(response.data.discount_amount);
            
            // Store coupon in session
            this.storeAppliedCoupon(response.data.coupon, response.data.discount_amount);
        } else {
            ajaxUtils.showMessage(response.data.error || 'Invalid coupon code', 'error');
        }

        ajaxUtils.hideLoading(submitBtn);
        form.reset();
    }

    displayAppliedCoupon(couponData) {
        const couponDisplay = document.getElementById('applied-coupon-display');
        if (!couponDisplay) return;

        couponDisplay.innerHTML = `
            <div class="applied-coupon bg-green-50 border border-green-200 rounded-lg p-4">
                <div class="flex justify-between items-center">
                    <div>
                        <h4 class="font-semibold text-green-800">${couponData.coupon.name}</h4>
                        <p class="text-green-600 text-sm">${couponData.coupon.code} - ${this.getDiscountDisplay(couponData.coupon)}</p>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="text-green-700 font-bold">-$${couponData.discount_amount}</span>
                        <button type="button" class="remove-coupon-btn text-red-500 hover:text-red-700">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Hide coupon form
        const couponForm = document.getElementById('apply-coupon-form');
        if (couponForm) {
            couponForm.style.display = 'none';
        }
    }

    async removeCoupon() {
        const response = await ajaxUtils.makeRequest('/api/coupons/remove/', 'POST');

        if (response.success) {
            ajaxUtils.showMessage('Coupon removed');
            this.clearAppliedCoupon();
            this.updateOrderTotals(0); // Reset totals
        } else {
            ajaxUtils.showMessage('Failed to remove coupon', 'error');
        }
    }

    clearAppliedCoupon() {
        const couponDisplay = document.getElementById('applied-coupon-display');
        const couponForm = document.getElementById('apply-coupon-form');
        
        if (couponDisplay) couponDisplay.innerHTML = '';
        if (couponForm) couponForm.style.display = 'block';
        
        // Clear stored coupon
        sessionStorage.removeItem('applied_coupon');
    }

    updateOrderTotals(discountAmount) {
        // Update checkout totals
        const subtotalEl = document.getElementById('checkout-subtotal');
        const discountEl = document.getElementById('checkout-discount');
        const totalEl = document.getElementById('checkout-total');

        if (subtotalEl && discountEl && totalEl) {
            const subtotal = parseFloat(subtotalEl.dataset.amount);
            const discount = parseFloat(discountAmount);
            const total = subtotal - discount;

            discountEl.textContent = `-$${discount.toFixed(2)}`;
            totalEl.textContent = `$${total.toFixed(2)}`;
        }
    }

    storeAppliedCoupon(coupon, discountAmount) {
        sessionStorage.setItem('applied_coupon', JSON.stringify({
            coupon: coupon,
            discount_amount: discountAmount,
            applied_at: new Date().toISOString()
        }));
    }

    getAppliedCoupon() {
        const stored = sessionStorage.getItem('applied_coupon');
        return stored ? JSON.parse(stored) : null;
    }

    getDiscountDisplay(coupon) {
        switch (coupon.discount_type) {
            case 'percentage':
                return `${coupon.discount_value}% off`;
            case 'fixed':
                return `$${coupon.discount_value} off`;
            case 'shipping':
                return 'Free shipping';
            default:
                return 'Discount';
        }
    }

    async loadAvailableCoupons() {
        const container = document.getElementById('available-coupons');
        if (!container) return;

        const response = await ajaxUtils.makeRequest('/api/coupons/available/');

        if (response.success) {
            this.renderAvailableCoupons(container, response.data);
        }
    }

    renderAvailableCoupons(container, coupons) {
        if (!coupons || coupons.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No coupons available at the moment.</p>';
            return;
        }

        container.innerHTML = coupons.map(coupon => `
            <div class="coupon-card bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <h4 class="font-semibold text-lg">${coupon.name}</h4>
                        <p class="text-gray-600 text-sm">${coupon.description}</p>
                    </div>
                    <span class="coupon-badge bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm font-medium">
                        ${this.getDiscountDisplay(coupon)}
                    </span>
                </div>
                
                <div class="flex justify-between items-center mt-3">
                    <div class="text-xs text-gray-500">
                        <span class="code-container">
                            Code: <strong>${coupon.code}</strong>
                            <button class="copy-coupon-btn ml-1 text-blue-600 hover:text-blue-800" 
                                    data-code="${coupon.code}">
                                <i class="fas fa-copy"></i>
                            </button>
                        </span>
                        ${coupon.minimum_order_amount > 0 ? 
                            `<br>Min. order: $${coupon.minimum_order_amount}` : ''}
                        ${coupon.valid_until ? 
                            `<br>Valid until: ${new Date(coupon.valid_until).toLocaleDateString()}` : ''}
                    </div>
                    
                    <button class="apply-coupon-btn btn-secondary btn-sm" 
                            data-code="${coupon.code}">
                        Apply
                    </button>
                </div>
            </div>
        `).join('');

        // Add event listeners to apply buttons
        container.querySelectorAll('.apply-coupon-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const code = btn.dataset.code;
                this.autoApplyCoupon(code);
            });
        });
    }

    async autoApplyCoupon(code) {
        const orderAmount = document.getElementById('checkout-subtotal')?.dataset.amount || 0;
        const form = document.getElementById('apply-coupon-form');
        
        if (form) {
            form.querySelector('input[name="coupon_code"]').value = code;
            this.applyCoupon(form);
        }
    }

    async copyCouponCode(button) {
        const code = button.dataset.code;
        
        try {
            await navigator.clipboard.writeText(code);
            ajaxUtils.showMessage('Coupon code copied to clipboard!');
            
            // Visual feedback
            const originalHtml = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i>';
            button.classList.add('text-green-600');
            
            setTimeout(() => {
                button.innerHTML = originalHtml;
                button.classList.remove('text-green-600');
            }, 2000);
        } catch (err) {
            console.error('Failed to copy coupon code:', err);
            ajaxUtils.showMessage('Failed to copy coupon code', 'error');
        }
    }

    // Admin coupon functions
    async generateCouponCode() {
        const response = await ajaxUtils.makeRequest('/api/coupons/generate-code/', 'POST');
        
        if (response.success) {
            const codeInput = document.getElementById('id_code');
            if (codeInput) {
                codeInput.value = response.data.code;
                ajaxUtils.showMessage('Coupon code generated!');
            }
        }
    }

    async bulkAssignCoupons() {
        const form = document.getElementById('bulk-assign-form');
        if (!form) return;

        const formData = new FormData(form);
        const userIds = Array.from(formData.getAll('user_ids'));
        const couponId = formData.get('coupon_id');

        if (!userIds.length || !couponId) {
            ajaxUtils.showMessage('Please select users and a coupon', 'error');
            return;
        }

        const response = await ajaxUtils.makeRequest('/api/coupons/assign/', 'POST', {
            user_ids: userIds,
            coupon_id: couponId
        });

        if (response.success) {
            ajaxUtils.showMessage(`Coupon assigned to ${response.data.assigned_count} users`);
            form.reset();
        } else {
            ajaxUtils.showMessage('Failed to assign coupons', 'error');
        }
    }
}

// Initialize coupon manager
document.addEventListener('DOMContentLoaded', function() {
    new CouponManager();
});