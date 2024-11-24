// Form Validation and Handling
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registrationForm');
    
    if (form) {
        // Form Validation
        form.addEventListener('submit', function(event) {
            let isValid = true;
            
            // Clear previous errors
            form.querySelectorAll('.is-invalid').forEach(el => {
                el.classList.remove('is-invalid');
            });
            
            // Validate required fields
            form.querySelectorAll('[required]').forEach(field => {
                if (!field.value) {
                    field.classList.add('is-invalid');
                    isValid = false;
                }
            });
            
            // Validate patterns
            form.querySelectorAll('[pattern]').forEach(field => {
                if (field.value && field.pattern) {
                    const pattern = new RegExp(field.pattern);
                    if (!pattern.test(field.value)) {
                        field.classList.add('is-invalid');
                        isValid = false;
                    }
                }
            });
            
            // Validate email fields
            form.querySelectorAll('input[type="email"]').forEach(field => {
                if (field.value && !isValidEmail(field.value)) {
                    field.classList.add('is-invalid');
                    isValid = false;
                }
            });
            
            // Validate file sizes
            form.querySelectorAll('input[type="file"]').forEach(field => {
                if (field.files.length > 0) {
                    const maxSize = parseInt(field.dataset.maxSize) * 1024 * 1024; // Convert to bytes
                    if (field.files[0].size > maxSize) {
                        field.classList.add('is-invalid');
                        isValid = false;
                    }
                }
            });
            
            if (!isValid) {
                event.preventDefault();
                // Scroll to first error
                const firstError = form.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
        
        // File Input Handlers
        form.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', function() {
                if (this.files.length > 0) {
                    const maxSize = parseInt(this.dataset.maxSize) * 1024 * 1024; // Convert to bytes
                    if (this.files[0].size > maxSize) {
                        alert(`File size must not exceed ${this.dataset.maxSize}MB`);
                        this.value = '';
                        return;
                    }
                    
                    // Show selected filename
                    const fileInfo = this.closest('.file-upload').querySelector('.file-info');
                    if (fileInfo) {
                        fileInfo.textContent = `Selected: ${this.files[0].name}`;
                    }
                }
            });
        });
    }
});

// Helper Functions
function isValidEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

// Custom Validation Messages
function updateValidationMessage(field, message) {
    const feedback = field.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
        feedback.textContent = message;
    }
}

// Handle Enter Key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && event.target.matches('input:not([type="submit"])')) {
        event.preventDefault();
        const form = event.target.form;
        const index = Array.prototype.indexOf.call(form, event.target);
        form.elements[index + 1].focus();
    }
});