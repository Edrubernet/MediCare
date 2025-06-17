/**
 * Medicare Core JavaScript
 * Main functionality for the Medicare application
 */

// Global Medicare namespace
window.Medicare = window.Medicare || {};

(function() {
    'use strict';

    // Configuration
    const config = {
        csrfTokenName: 'csrfmiddlewaretoken',
        loadingClass: 'loading',
        fadeInClass: 'fade-in',
        animationDuration: 300
    };

    // Utility functions
    const utils = {
        // Get CSRF token from form or meta tag
        getCsrfToken: function() {
            const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
            return token;
        },

        // Show loading state on element
        showLoading: function(element) {
            if (element) {
                element.classList.add(config.loadingClass);
                element.disabled = true;
            }
        },

        // Hide loading state on element
        hideLoading: function(element) {
            if (element) {
                element.classList.remove(config.loadingClass);
                element.disabled = false;
            }
        },

        // Show toast notification
        showToast: function(message, type = 'info') {
            const toastContainer = this.getOrCreateToastContainer();
            const toast = this.createToast(message, type);
            toastContainer.appendChild(toast);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                toast.remove();
            }, 5000);
        },

        // Get or create toast container
        getOrCreateToastContainer: function() {
            let container = document.getElementById('toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toast-container';
                container.className = 'toast-container position-fixed top-0 end-0 p-3';
                container.style.zIndex = '1055';
                document.body.appendChild(container);
            }
            return container;
        },

        // Create toast element
        createToast: function(message, type) {
            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type} border-0`;
            toast.setAttribute('role', 'alert');
            
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;
            
            // Initialize Bootstrap toast
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
            
            return toast;
        },

        // Debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Format date for display
        formatDate: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('uk-UA', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
        },

        // Format datetime for display
        formatDateTime: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('uk-UA', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    };

    // AJAX helpers
    const ajax = {
        // Generic AJAX request
        request: function(url, options = {}) {
            const defaults = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': utils.getCsrfToken()
                }
            };

            const config = Object.assign({}, defaults, options);
            
            return fetch(url, config)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .catch(error => {
                    console.error('AJAX Error:', error);
                    utils.showToast('Помилка при виконанні запиту', 'danger');
                    throw error;
                });
        },

        // GET request
        get: function(url) {
            return this.request(url);
        },

        // POST request
        post: function(url, data) {
            return this.request(url, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        // PUT request
        put: function(url, data) {
            return this.request(url, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },

        // DELETE request
        delete: function(url) {
            return this.request(url, {
                method: 'DELETE'
            });
        }
    };

    // Form helpers
    const forms = {
        // Initialize form handlers
        init: function() {
            this.setupFormValidation();
            this.setupAjaxForms();
            this.setupFileUploads();
        },

        // Setup form validation
        setupFormValidation: function() {
            const forms = document.querySelectorAll('.needs-validation');
            forms.forEach(form => {
                form.addEventListener('submit', (event) => {
                    if (!form.checkValidity()) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                    form.classList.add('was-validated');
                });
            });
        },

        // Setup AJAX forms
        setupAjaxForms: function() {
            const ajaxForms = document.querySelectorAll('.ajax-form');
            ajaxForms.forEach(form => {
                form.addEventListener('submit', (event) => {
                    event.preventDefault();
                    this.submitAjaxForm(form);
                });
            });
        },

        // Submit AJAX form
        submitAjaxForm: function(form) {
            const submitBtn = form.querySelector('button[type="submit"]');
            const url = form.action;
            const formData = new FormData(form);

            utils.showLoading(submitBtn);

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': utils.getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    utils.showToast(data.message || 'Операція виконана успішно', 'success');
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    }
                } else {
                    utils.showToast(data.message || 'Виникла помилка', 'danger');
                }
            })
            .catch(error => {
                console.error('Form submission error:', error);
                utils.showToast('Помилка при відправці форми', 'danger');
            })
            .finally(() => {
                utils.hideLoading(submitBtn);
            });
        },

        // Setup file upload handlers
        setupFileUploads: function() {
            const fileInputs = document.querySelectorAll('input[type="file"]');
            fileInputs.forEach(input => {
                input.addEventListener('change', (event) => {
                    this.handleFileUpload(event.target);
                });
            });
        },

        // Handle file upload
        handleFileUpload: function(input) {
            const files = input.files;
            const maxSize = 10 * 1024 * 1024; // 10MB
            const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];

            for (let file of files) {
                if (file.size > maxSize) {
                    utils.showToast('Файл занадто великий. Максимальний розмір: 10MB', 'warning');
                    input.value = '';
                    return;
                }

                if (!allowedTypes.includes(file.type)) {
                    utils.showToast('Непідтримуваний тип файлу', 'warning');
                    input.value = '';
                    return;
                }
            }
        }
    };

    // UI enhancements
    const ui = {
        // Initialize UI enhancements
        init: function() {
            this.setupTooltips();
            this.setupPopovers();
            this.setupTables();
            this.setupSearchFilters();
            this.setupAnimations();
        },

        // Setup Bootstrap tooltips
        setupTooltips: function() {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        },

        // Setup Bootstrap popovers
        setupPopovers: function() {
            const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
            popoverTriggerList.map(function (popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl);
            });
        },

        // Setup table enhancements
        setupTables: function() {
            // Add sorting functionality
            const sortableHeaders = document.querySelectorAll('.sortable');
            sortableHeaders.forEach(header => {
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => {
                    this.sortTable(header);
                });
            });

            // Add row hover effects
            const tables = document.querySelectorAll('.table');
            tables.forEach(table => {
                table.classList.add('table-hover');
            });
        },

        // Sort table by column
        sortTable: function(header) {
            const table = header.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const columnIndex = Array.from(header.parentNode.children).indexOf(header);
            const isAscending = header.classList.contains('sort-asc');

            rows.sort((a, b) => {
                const aText = a.children[columnIndex].textContent.trim();
                const bText = b.children[columnIndex].textContent.trim();
                
                const aVal = isNaN(aText) ? aText : parseFloat(aText);
                const bVal = isNaN(bText) ? bText : parseFloat(bText);
                
                if (isAscending) {
                    return aVal > bVal ? -1 : 1;
                } else {
                    return aVal < bVal ? -1 : 1;
                }
            });

            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));

            // Update sort classes
            header.parentNode.querySelectorAll('th').forEach(th => {
                th.classList.remove('sort-asc', 'sort-desc');
            });
            header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
        },

        // Setup search filters
        setupSearchFilters: function() {
            const searchInputs = document.querySelectorAll('.search-filter');
            searchInputs.forEach(input => {
                const targetSelector = input.dataset.target;
                if (targetSelector) {
                    input.addEventListener('input', utils.debounce((event) => {
                        this.filterElements(event.target.value, targetSelector);
                    }, 300));
                }
            });
        },

        // Filter elements based on search
        filterElements: function(searchTerm, targetSelector) {
            const elements = document.querySelectorAll(targetSelector);
            const term = searchTerm.toLowerCase();

            elements.forEach(element => {
                const text = element.textContent.toLowerCase();
                if (text.includes(term)) {
                    element.style.display = '';
                    element.classList.add(config.fadeInClass);
                } else {
                    element.style.display = 'none';
                    element.classList.remove(config.fadeInClass);
                }
            });
        },

        // Setup animations
        setupAnimations: function() {
            // Animate elements on scroll
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add(config.fadeInClass);
                    }
                });
            });

            document.querySelectorAll('.animate-on-scroll').forEach(el => {
                observer.observe(el);
            });
        }
    };

    // Initialize everything when DOM is ready
    function init() {
        forms.init();
        ui.init();
        
        // Add fade-in class to main content
        const mainContent = document.querySelector('main, .container');
        if (mainContent) {
            mainContent.classList.add(config.fadeInClass);
        }

        console.log('Medicare JavaScript initialized');
    }

    // Expose public API
    Medicare.utils = utils;
    Medicare.ajax = ajax;
    Medicare.forms = forms;
    Medicare.ui = ui;
    Medicare.init = init;

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

// Global helper functions for backward compatibility
function showToast(message, type = 'info') {
    Medicare.utils.showToast(message, type);
}

function getCsrfToken() {
    return Medicare.utils.getCsrfToken();
}

function formatDate(dateString) {
    return Medicare.utils.formatDate(dateString);
}

function formatDateTime(dateString) {
    return Medicare.utils.formatDateTime(dateString);
}