/**
 * Job Tracker - Main JavaScript
 * Basic interactivity and helpers
 */

// ============================================================================
// ALERT/FLASH MESSAGE HANDLING
// ============================================================================

/**
 * Close an alert message
 */
function closeAlert(element) {
    element.style.opacity = '0';
    setTimeout(() => {
        element.remove();
    }, 300);
}

// Auto-dismiss success messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const successAlerts = document.querySelectorAll('.alert-success');
    successAlerts.forEach(alert => {
        setTimeout(() => {
            closeAlert(alert);
        }, 5000);
    });
});


// ============================================================================
// MODAL HANDLING
// ============================================================================

/**
 * Open a modal by ID
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Close a modal by ID
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Close modal on overlay click
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal(e.target.id);
    }
});

// Close modal on ESC key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal-overlay[style*="display: flex"]');
        openModals.forEach(modal => {
            closeModal(modal.id);
        });
    }
});


// ============================================================================
// CONFIRMATION DIALOGS
// ============================================================================

/**
 * Confirm before deleting something
 */
function confirmDelete(itemName) {
    return confirm(`Are you sure you want to delete "${itemName}"? This cannot be undone.`);
}

/**
 * Confirm before clearing/resetting
 */
function confirmClear(message) {
    return confirm(message || 'Are you sure? This cannot be undone.');
}

// Add confirmation to delete buttons
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const itemName = this.dataset.confirmDelete;
            if (!confirmDelete(itemName)) {
                e.preventDefault();
                return false;
            }
        });
    });
});


// ============================================================================
// FORM ENHANCEMENTS
// ============================================================================

/**
 * Show loading state on form submission
 */
function showLoadingState(form) {
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.dataset.originalText = submitButton.textContent;
        submitButton.innerHTML = '<span class="spinner"></span> Loading...';
    }
}

// Add loading state to forms with data-loading attribute
document.addEventListener('DOMContentLoaded', function() {
    const formsWithLoading = document.querySelectorAll('form[data-loading]');
    formsWithLoading.forEach(form => {
        form.addEventListener('submit', function() {
            showLoadingState(this);
        });
    });
});


// ============================================================================
// DROPDOWN MENUS
// ============================================================================

/**
 * Toggle dropdown menu
 */
function toggleDropdown(button) {
    const dropdown = button.nextElementSibling;
    if (dropdown && dropdown.classList.contains('dropdown-menu')) {
        const isOpen = dropdown.style.display === 'block';
        // Close all dropdowns first
        document.querySelectorAll('.dropdown-menu').forEach(d => {
            d.style.display = 'none';
        });
        // Toggle this dropdown
        dropdown.style.display = isOpen ? 'none' : 'block';
    }
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('.nav-dropdown')) {
        document.querySelectorAll('.dropdown-menu').forEach(dropdown => {
            dropdown.style.display = 'none';
        });
    }
});


// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show temporary success message
        const message = document.createElement('div');
        message.className = 'alert alert-success';
        message.textContent = 'Copied to clipboard!';
        message.style.position = 'fixed';
        message.style.top = '20px';
        message.style.right = '20px';
        message.style.zIndex = '9999';
        document.body.appendChild(message);
        
        setTimeout(() => {
            message.remove();
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

/**
 * Debounce function for search inputs
 */
function debounce(func, wait) {
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


// ============================================================================
// TABLE ENHANCEMENTS
// ============================================================================

/**
 * Make table rows clickable
 */
document.addEventListener('DOMContentLoaded', function() {
    const clickableRows = document.querySelectorAll('tr[data-href]');
    clickableRows.forEach(row => {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking a button or link
            if (!e.target.closest('button, a')) {
                window.location.href = this.dataset.href;
            }
        });
    });
});


// ============================================================================
// ACCESSIBILITY HELPERS
// ============================================================================

/**
 * Trap focus within modal
 */
function trapFocus(element) {
    const focusableElements = element.querySelectorAll(
        'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    element.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                if (document.activeElement === firstFocusable) {
                    lastFocusable.focus();
                    e.preventDefault();
                }
            } else {
                if (document.activeElement === lastFocusable) {
                    firstFocusable.focus();
                    e.preventDefault();
                }
            }
        }
    });
}

// Apply focus trap to modals
document.addEventListener('DOMContentLoaded', function() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(trapFocus);
});


// ============================================================================
// CONSOLE BRANDING
// ============================================================================

console.log(
    '%c🎯 Job Tracker %cv2.0',
    'font-size: 20px; font-weight: bold; color: #3490dc;',
    'font-size: 12px; color: #6c757d;'
);
console.log('Made with ❤️ to make job applications less painful');
