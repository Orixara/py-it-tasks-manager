document.addEventListener('DOMContentLoaded', function() {
    initStatusOptions();
});

function initStatusOptions() {
    document.querySelectorAll('.status-option').forEach(function(option) {
        option.addEventListener('click', handleStatusChange);
    });
}

function handleStatusChange(e) {
    e.preventDefault();

    const taskId = this.getAttribute('data-task-id');
    const newStatus = this.getAttribute('data-status');
    const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
    const currentStatus = taskCard ? taskCard.getAttribute('data-current-status') : null;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        showErrorToast('CSRF token not found');
        return;
    }

    const formData = new FormData();
    formData.append('status', newStatus);
    formData.append('csrfmiddlewaretoken', csrfToken.value);

    const url = `/task/${taskId}/toggle-status/`;

    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            updateTaskUI(taskId, data);
            updateDropdownOptions(taskId, currentStatus, data.status_key);

            if (taskCard) {
                taskCard.setAttribute('data-current-status', data.status_key);
            }

            showStatusToast(data.new_status);
        }
    })
    .catch(error => {
        showErrorToast('Failed to update status. Please try again.');
    });
}

function updateTaskUI(taskId, data) {
    const statusSpan = document.getElementById('status-' + taskId);
    
    const icons = {
        'todo': '⏱',
        'in_progress': '🔄',
        'review': '👁️',
        'done': '✓'
    };

    const colors = {
        'todo': 'text-warning',
        'in_progress': 'text-info',
        'review': 'text-primary',
        'done': 'text-success'
    };
    
    if (statusSpan) {
        const card = statusSpan.closest('.task-card');

        if (card) {
            card.classList.add('status-updating');
        }

        setTimeout(() => {
            statusSpan.innerHTML = `<span class="${colors[data.status_key]} fw-bold">${icons[data.status_key]} ${data.new_status}</span>`;

            if (card) {
                card.classList.remove('border-warning', 'border-info', 'border-primary', 'border-success', 'opacity-75', 'status-updating');

                const borderClasses = {
                    'todo': 'border-warning',
                    'in_progress': 'border-info', 
                    'review': 'border-primary',
                    'done': 'border-success'
                };

                card.classList.add(borderClasses[data.status_key]);

                if (data.status_key === 'done') {
                    card.classList.add('opacity-75');
                }
            }
        }, 200);
    }

    const statusAlert = document.getElementById('task-status-alert');
    if (statusAlert) {
        updateStatusAlert(statusAlert, data);
    }
}

function updateStatusAlert(statusAlert, data) {
    statusAlert.classList.add('status-updating');

    setTimeout(() => {
        const alertClasses = {
            'todo': 'alert-warning',
            'in_progress': 'alert-info',
            'review': 'alert-primary',
            'done': 'alert-success'
        };

        const iconClasses = {
            'todo': 'bi-clock',
            'in_progress': 'bi-arrow-clockwise',
            'review': 'bi-eye',
            'done': 'bi-check-circle'
        };

        statusAlert.className = `alert ${alertClasses[data.status_key]}`;
        statusAlert.innerHTML = `
            <i class="${iconClasses[data.status_key]}"></i> 
            Status: ${data.new_status}
        `;

        statusAlert.classList.remove('status-updating');
        statusAlert.classList.add('status-updated');

        setTimeout(() => {
            statusAlert.classList.remove('status-updated');
        }, 600);
    }, 300);
}

function updateDropdownOptions(taskId, oldStatus, newStatus) {
    const statusOptions = document.querySelectorAll(`[data-task-id="${taskId}"].status-option`);
    
    if (statusOptions.length === 0) return;

    const dropdown = statusOptions[0].closest('.dropdown-menu');
    if (!dropdown) return;

    const statusData = {
        'todo': { label: 'To Do' },
        'in_progress': { label: 'In Progress' },
        'review': { label: 'Review' },
        'done': { label: 'Done' }
    };

    const newStatusOption = dropdown.querySelector(`[data-task-id="${taskId}"][data-status="${newStatus}"]`);
    if (newStatusOption) {
        newStatusOption.closest('li').remove();
    }

    if (oldStatus && !dropdown.querySelector(`[data-task-id="${taskId}"][data-status="${oldStatus}"]`)) {
        const li = document.createElement('li');
        const statusInfo = statusData[oldStatus];
        
        li.innerHTML = `
            <button class="dropdown-item status-option" 
                    data-task-id="${taskId}" 
                    data-status="${oldStatus}">
                ${statusInfo.label}
            </button>
        `;
        
        insertOptionInOrder(dropdown, li, oldStatus);
        const newOption = li.querySelector('.status-option');
        newOption.addEventListener('click', handleStatusChange);
    }
}

function insertOptionInOrder(dropdown, newLi, status) {
    const statusOrder = ['todo', 'in_progress', 'review', 'done'];
    const statusIndex = statusOrder.indexOf(status);
    
    const existingOptions = dropdown.querySelectorAll('.status-option');
    let inserted = false;
    
    for (let option of existingOptions) {
        const optionStatus = option.getAttribute('data-status');
        const optionIndex = statusOrder.indexOf(optionStatus);
        
        if (statusIndex < optionIndex) {
            option.closest('li').parentElement.insertBefore(newLi, option.closest('li'));
            inserted = true;
            break;
        }
    }
    
    if (!inserted) {
        dropdown.appendChild(newLi);
    }
}

function showStatusToast(newStatus) {
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1060';
        document.body.appendChild(toastContainer);
    }

    const toastId = 'status-toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast show';
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="toast-header">
            <i class="bi bi-check-circle-fill text-success me-2"></i>
            <strong class="me-auto">Status Updated</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            Task status changed to: <strong>${newStatus}</strong>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        if (document.getElementById(toastId)) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }
    }, 4000);
}

function showErrorToast(message) {
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1060';
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'error-toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast show';
    toast.innerHTML = `
        <div class="toast-header">
            <i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>
            <strong class="me-auto">Error</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        if (document.getElementById(toastId)) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}
