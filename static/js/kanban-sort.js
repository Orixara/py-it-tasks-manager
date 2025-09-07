(function() {
  'use strict';

  const PRIORITY_ORDER = {
    'urgent': 4,
    'high': 3,
    'medium': 2,
    'low': 1
  };

  function addSortControls() {
    document.querySelectorAll('.drop-zone').forEach(zone => {
      const card = zone.closest('.card');
      const header = card.querySelector('.card-header');
      
      if (!header.querySelector('.sort-controls')) {
        const sortControls = document.createElement('div');
        sortControls.className = 'sort-controls float-end';
        sortControls.innerHTML = `
          <div class="btn-group btn-group-sm" role="group">
            <button type="button" class="btn btn-outline-light btn-sort" 
                    data-sort="deadline" data-zone="${zone.dataset.status}" 
                    title="Sort by deadline">
              <i class="bi bi-calendar"></i>
            </button>
            <button type="button" class="btn btn-outline-light btn-sort" 
                    data-sort="priority" data-zone="${zone.dataset.status}"
                    title="Sort by priority">
              <i class="bi bi-exclamation-triangle"></i>
            </button>
            <button type="button" class="btn btn-outline-light btn-sort" 
                    data-sort="name" data-zone="${zone.dataset.status}"
                    title="Sort by name">
              <i class="bi bi-sort-alpha-down"></i>
            </button>
          </div>
        `;
        header.appendChild(sortControls);
      }
    });
  }

  function getTaskData(card) {
    const name = card.querySelector('.card-title')?.textContent.trim() || '';
    const deadlineText = card.querySelector('small:last-child')?.textContent.trim() || '';
    const priorityBadge = card.querySelector('.badge:not(.bg-secondary):not(.bg-light)');
    let priority = 'medium';
    
    if (priorityBadge) {
      const classList = Array.from(priorityBadge.classList);
      if (classList.includes('bg-urgent')) priority = 'urgent';
      else if (classList.includes('bg-high')) priority = 'high';
      else if (classList.includes('bg-low')) priority = 'low';
    }

    let deadlineSort = new Date().getTime(); // default to today
    if (deadlineText) {
      const currentYear = new Date().getFullYear();
      try {
        const parsed = new Date(`${deadlineText} ${currentYear}`);
        if (!isNaN(parsed.getTime())) {
          deadlineSort = parsed.getTime();
        }
      } catch (e) {
      }
    }

    return {
      element: card,
      name: name.toLowerCase(),
      priority: priority,
      priorityValue: PRIORITY_ORDER[priority] || 2,
      deadline: deadlineSort,
      deadlineText: deadlineText
    };
  }

  function sortTasks(zone, sortBy) {
    const container = zone.querySelector('.kanban-items');
    if (!container) return;

    const cards = Array.from(container.querySelectorAll('.task-card'));
    if (cards.length <= 1) return;

    const taskData = cards.map(getTaskData);

    taskData.sort((a, b) => {
      switch (sortBy) {
        case 'deadline':
          return a.deadline - b.deadline; // Earliest first
        case 'priority':
          return b.priorityValue - a.priorityValue; // Highest priority first
        case 'name':
          return a.name.localeCompare(b.name); // Alphabetical
        default:
          return 0;
      }
    });

    const fragment = document.createDocumentFragment();
    taskData.forEach(task => {
      fragment.appendChild(task.element);
    });
    container.appendChild(fragment);

    showSortFeedback(zone, sortBy);
  }

  function showSortFeedback(zone, sortBy) {
    const card = zone.closest('.card');
    const header = card.querySelector('.card-header');
    const oldFeedback = header.querySelector('.sort-feedback');
    if (oldFeedback) oldFeedback.remove();

    const feedback = document.createElement('small');
    feedback.className = 'sort-feedback text-light ms-2';
    feedback.innerHTML = `<i class="bi bi-check"></i> Sorted by ${sortBy}`;
    header.appendChild(feedback);

    setTimeout(() => {
      if (feedback && feedback.parentNode) {
        feedback.remove();
      }
    }, 3000);
  }

  document.addEventListener('click', function(e) {
    if (e.target.closest('.btn-sort')) {
      const btn = e.target.closest('.btn-sort');
      const sortBy = btn.dataset.sort;
      const zoneStatus = btn.dataset.zone;
      const zone = document.querySelector(`[data-status="${zoneStatus}"]`);
      
      if (zone) {
        sortTasks(zone, sortBy);

        const controls = btn.closest('.sort-controls');
        controls.querySelectorAll('.btn-sort').forEach(b => {
          b.classList.remove('btn-light');
          b.classList.add('btn-outline-light');
        });
        btn.classList.remove('btn-outline-light');
        btn.classList.add('btn-light');

        setTimeout(() => {
          btn.classList.remove('btn-light');
          btn.classList.add('btn-outline-light');
        }, 2000);
      }
    }
  });

  document.addEventListener('DOMContentLoaded', function() {
    addSortControls();
  });
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addSortControls);
  } else {
    addSortControls();
  }
})();
