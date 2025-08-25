document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.status-option').forEach(function(option) {
        option.addEventListener('click', function(e) {
            e.preventDefault();

            const taskId = this.getAttribute('data-task-id');
            const newStatus = this.getAttribute('data-status');
            const statusSpan = document.getElementById('status-' + taskId);

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (!csrfToken) {
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

                    statusSpan.innerHTML = `<span class="${colors[data.status_key]} fw-bold">${icons[data.status_key]} ${data.new_status}</span>`;

                    const card = statusSpan.closest('.card');

                    card.classList.remove('border-warning', 'border-info', 'border-primary', 'border-success', 'opacity-75');

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
            })
            .catch(error => {
                console.error('Error updating status:', error);
            });
        });
    });
});