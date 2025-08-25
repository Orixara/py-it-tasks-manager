(function () {
  "use strict";

  function getCsrfToken() {
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    if (input) return input.value;
    const m = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }
  const CSRF = getCsrfToken();

  const DRAGGED_CLASS = "opacity-50";
  const ACTIVE_ZONE_CLASS = "dropzone--active";

  function getItemsContainer(zone) {
    return zone.querySelector(".kanban-items") || zone;
  }
  function getEmptyNode(zone) {
    return zone.querySelector(".kanban-empty");
  }
  function getCountBadge(zone) {
    const card = zone.closest(".card");
    return card ? card.querySelector(".kanban-count") : null;
  }
  function countCards(zone) {
    return getItemsContainer(zone).querySelectorAll(".task-card").length;
  }
  function updateZoneState(zone) {
    const n = countCards(zone);
    const empty = getEmptyNode(zone);
    if (empty) empty.classList.toggle("d-none", n > 0);
    const badge = getCountBadge(zone);
    if (badge) badge.textContent = n;
  }
  function updateAllZonesState() {
    document.querySelectorAll(".drop-zone").forEach(updateZoneState);
  }

  function disableInnerNativeDnD(card) {
    card.querySelectorAll("a, img, button").forEach((el) => {
      el.setAttribute("draggable", "false");
    });
  }

  function attachCardHandlers(card) {
    if (card.__dndBound) return;
    card.__dndBound = true;

    if (card.dataset.canModify === "0") {
      card.setAttribute("draggable", "false");
      card.style.cursor = "default";
      card.classList.add("opacity-50");
      return;
    }
    
    card.setAttribute("draggable", "true");
    disableInnerNativeDnD(card);

    card.addEventListener("dragstart", onDragStart);
    card.addEventListener("dragend", onDragEnd);
  }
  function attachAllCards() {
    document.querySelectorAll(".task-card").forEach(attachCardHandlers);
  }

  let draggedEl = null;
  let originZone = null;
  let originNextSibling = null;
  let isDropping = false;
  let disabledAnchorStyles = [];

  document.addEventListener("DOMContentLoaded", () => {
    attachAllCards();
    document.querySelectorAll(".drop-zone").forEach((zone) => {
      zone.addEventListener("dragover", (e) => onDragOver(e, zone));
      zone.addEventListener("dragenter", (e) => onDragEnter(e, zone));
      zone.addEventListener("dragleave", (e) => onDragLeave(e, zone));
      zone.addEventListener("drop", (e) => onDrop(e, zone));
    });

    updateAllZonesState();
  });

  function onDragStart(e) {
    const card = e.currentTarget;

    if (card.dataset.canModify === "0") {
      e.preventDefault();
      return false;
    }
    
    draggedEl = card;
    draggedEl.classList.add(DRAGGED_CLASS);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", draggedEl.dataset.taskId);

    originZone = draggedEl.closest(".drop-zone");
    originNextSibling = draggedEl.nextElementSibling;

    disabledAnchorStyles = [];
    draggedEl.querySelectorAll("a").forEach((a) => {
      disabledAnchorStyles.push([a, a.style.pointerEvents]);
      a.style.pointerEvents = "none";
    });
  }

  function onDragEnd() {
    if (draggedEl) {
      draggedEl.classList.remove(DRAGGED_CLASS);
      disabledAnchorStyles.forEach(([a, prev]) => (a.style.pointerEvents = prev || ""));
      disabledAnchorStyles = [];
    }
    draggedEl = null;
    originZone = null;
    originNextSibling = null;
    isDropping = false;

    document.querySelectorAll("." + ACTIVE_ZONE_CLASS).forEach((z) => {
      z.classList.remove(ACTIVE_ZONE_CLASS);
    });
  }

  function onDragOver(e, zone) {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  }
  function onDragEnter(e, zone) {
    zone.classList.add(ACTIVE_ZONE_CLASS);
  }
  function onDragLeave(e, zone) {
    if (!zone.contains(e.relatedTarget)) {
      zone.classList.remove(ACTIVE_ZONE_CLASS);
    }
  }

  async function onDrop(e, zone) {
    e.preventDefault();
    if (!draggedEl || isDropping) return;

    zone.classList.remove(ACTIVE_ZONE_CLASS);

    const targetStatus = zone.dataset.status;
    const taskId = draggedEl.dataset.taskId;
    const prevStatus = draggedEl.dataset.currentStatus;

    if (!targetStatus) return;

    isDropping = true;

    const targetList = getItemsContainer(zone);
    const placeholder = document.createElement("div");
    placeholder.style.height = draggedEl.offsetHeight + "px";
    draggedEl.parentNode.insertBefore(placeholder, draggedEl);
    targetList.appendChild(draggedEl);

    draggedEl.dataset.currentStatus = targetStatus;
    if (targetStatus === "done") draggedEl.classList.add("opacity-75");
    else draggedEl.classList.remove("opacity-75");

    if (originZone) updateZoneState(originZone);
    updateZoneState(zone);

    try {
      const formData = new FormData();
      formData.append("status", targetStatus);
      formData.append("csrfmiddlewaretoken", CSRF);

      const resp = await fetch(`/task/${taskId}/toggle-status/`, {
        method: "POST",
        body: formData,
      });
      
      if (resp.status === 403) {
        throw new Error("You don't have permission to modify this task");
      }
      
      if (!resp.ok) {
        const errorData = await resp.json();
        throw new Error(errorData.error || `Server responded ${resp.status}`);
      }

      attachCardHandlers(draggedEl);
      updateAllZonesState();
    } catch (err) {
      if (placeholder && placeholder.parentNode) {
        placeholder.parentNode.insertBefore(draggedEl, placeholder);
      } else if (originZone) {
        const originList = getItemsContainer(originZone);
        if (originNextSibling && originNextSibling.parentNode === originList) {
          originList.insertBefore(draggedEl, originNextSibling);
        } else {
          originList.appendChild(draggedEl);
        }
      }
      draggedEl.dataset.currentStatus = prevStatus;
      if (prevStatus === "done") draggedEl.classList.add("opacity-75");
      else draggedEl.classList.remove("opacity-75");

      if (originZone) updateZoneState(originZone);
      updateZoneState(zone);

      console.error(err);
      alert("Unable to update status. Please try again.");
    } finally {
      if (placeholder && placeholder.parentNode) {
        placeholder.parentNode.removeChild(placeholder);
      }
      isDropping = false;
    }
  }
})();
