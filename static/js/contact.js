class ContactManager {
    constructor() {
        this.initEventListeners();
        this.loadFAQs();
    }

    initEventListeners() {
        const contactForm = document.getElementById('contact-form');
        if (contactForm) {
            contactForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitContactForm(e.target);
            });
        }
    }

    async submitContactForm(form) {
        const formData = new FormData(form);
        const data = {
            name: formData.get('name'),
            email: formData.get('email'),
            subject: formData.get('subject'),
            message: formData.get('message')
        };

        // Clear previous errors
        this.clearErrors();

        // Basic validation
        if (!this.validateForm(data)) {
            return;
        }

        const button = form.querySelector('button[type="submit"]');
        ajaxUtils.showLoading(button, 'Sending...');

        try {
            const response = await ajaxUtils.makeRequest('/api/home/contact/', 'POST', data);

            if (response.success) {
                ajaxUtils.showMessage(response.data.message || 'Thank you for your message! We will get back to you soon.');
                form.reset();
            } else {
                this.displayErrors(response.data.errors);
            }
        } catch (error) {
            ajaxUtils.showMessage('Failed to send message. Please try again.', 'error');
        } finally {
            ajaxUtils.hideLoading(button);
        }
    }

    validateForm(data) {
        let isValid = true;

        if (!data.name || data.name.trim().length < 2) {
            this.displayError('name', 'Please enter your full name.');
            isValid = false;
        }

        if (!data.email || !this.isValidEmail(data.email)) {
            this.displayError('email', 'Please enter a valid email address.');
            isValid = false;
        }

        if (!data.subject || data.subject.trim().length < 5) {
            this.displayError('subject', 'Please enter a subject with at least 5 characters.');
            isValid = false;
        }

        if (!data.message || data.message.trim().length < 10) {
            this.displayError('message', 'Please enter a message with at least 10 characters.');
            isValid = false;
        }

        return isValid;
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    displayError(field, message) {
        const errorElement = document.getElementById(`${field}-error`);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        }

        const inputElement = document.getElementById(field);
        if (inputElement) {
            inputElement.classList.add('border-red-500');
        }
    }

    displayErrors(errors) {
        if (!errors) return;

        Object.keys(errors).forEach(field => {
            if (errors[field] && errors[field].length > 0) {
                this.displayError(field, errors[field][0]);
            }
        });
    }

    clearErrors() {
        const errorElements = document.querySelectorAll('.error-message');
        errorElements.forEach(element => {
            element.classList.add('hidden');
            element.textContent = '';
        });

        const inputElements = document.querySelectorAll('.form-input, .form-textarea');
        inputElements.forEach(element => {
            element.classList.remove('border-red-500');
        });
    }

    async loadFAQs() {
        const container = document.getElementById('faq-preview');
        if (!container) return;

        try {
            const response = await ajaxUtils.makeRequest('/api/home/faqs/');
            
            if (response.success && response.data.faqs) {
                let faqHTML = '';
                const categories = Object.keys(response.data.faqs).slice(0, 3); // Show first 3 categories
                
                categories.forEach(category => {
                    const faqs = response.data.faqs[category].slice(0, 2); // Show first 2 FAQs per category
                    
                    faqs.forEach(faq => {
                        faqHTML += `
                            <div class="faq-item border-b border-gray-200 pb-4">
                                <h4 class="font-semibold text-gray-800 mb-2">${faq.question}</h4>
                                <p class="text-gray-600 text-sm">${faq.answer.substring(0, 100)}...</p>
                            </div>
                        `;
                    });
                });

                container.innerHTML = faqHTML || '<p class="text-gray-500">No FAQs available.</p>';
            }
        } catch (error) {
            console.error('Failed to load FAQs:', error);
            container.innerHTML = '<p class="text-gray-500">Failed to load FAQs.</p>';
        }
    }
}

// Initialize contact page
document.addEventListener('DOMContentLoaded', function() {
    new ContactManager();
});