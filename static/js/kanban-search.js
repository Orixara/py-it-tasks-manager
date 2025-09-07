(function() {
  'use strict';

  let searchTimeouts = {};

  function performColumnSearch(input) {
    const column = input.dataset.column;
    const searchTerm = input.value.toLowerCase().trim();
    const dropZone = document.querySelector(`[data-status="${column}"]`);
    
    if (!dropZone) return;

    const cards = dropZone.querySelectorAll('.task-card');
    let visibleCount = 0;

    cards.forEach(card => {
      const title = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
      const description = card.querySelector('.card-text')?.textContent.toLowerCase() || '';
      const assignees = Array.from(card.querySelectorAll('.badge.bg-light'))
        .map(badge => badge.textContent.toLowerCase()).join(' ');

      const isVisible = !searchTerm || 
        title.includes(searchTerm) || 
        description.includes(searchTerm) || 
        assignees.includes(searchTerm);

      card.style.display = isVisible ? 'block' : 'none';
      if (isVisible) visibleCount++;
    });

    const emptyNode = dropZone.querySelector('.kanban-empty');
    if (emptyNode) {
      emptyNode.classList.toggle('d-none', visibleCount > 0);
    }

    const countBadge = dropZone.closest('.card').querySelector('.kanban-count');
    if (countBadge) {
      countBadge.textContent = visibleCount;
    }
  }

  function clearColumnSearch(column) {
    const input = document.querySelector(`[data-column="${column}"]`);
    if (input) {
      input.value = '';
      performColumnSearch(input);
    }
  }

  function clearAllSearches() {
    document.querySelectorAll('.kanban-search').forEach(input => {
      input.value = '';
      performColumnSearch(input);
    });
  }

  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.kanban-search').forEach(input => {
      input.addEventListener('input', function(e) {
        const column = e.target.dataset.column;
        if (searchTimeouts[column]) {
          clearTimeout(searchTimeouts[column]);
        }
        searchTimeouts[column] = setTimeout(() => {
          performColumnSearch(e.target);
        }, 300);
      });
      input.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
          e.target.value = '';
          performColumnSearch(e.target);
        }
      });
    });
    document.addEventListener('keydown', function(e) {
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        clearAllSearches();
        document.querySelector('.kanban-search').focus();
      }
    });
  });

  window.KanbanSearch = {
    clearColumn: clearColumnSearch,
    clearAll: clearAllSearches
  };
})();
