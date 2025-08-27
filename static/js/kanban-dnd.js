(function () {
  "use strict";

  function getCsrfToken() {
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    if (input) return input.value;
    const m = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }
  const CSRF = getCsrfToken();

  function detectAppPrefix() {
    const path = window.location.pathname;
    const m = path.match(/^(.*?\/app\/)/);
    if (m) return m[1];
    return path.endsWith("/") ? path : path.replace(/[^/]+$/, "");
  }

  function getToggleUrlFromCard(card) {
    const taskId = card.dataset.taskId;
    if (card.dataset && card.dataset.toggleUrl) return card.dataset.toggleUrl;
    const base = detectAppPrefix();
    const sep = base.endsWith("/") ? "" : "/";
    return `${base}${sep}task/${taskId}/toggle-status/`;
  }

  function normalizeStatusKey(s) {
    return (s || "").toLowerCase().replace(/-/g, "_");
  }

  function toastError(msg) {
    try {
      let container = document.querySelector(".toast-container");
      if (!container) {
        container = document.createElement("div");
        container.className = "toast-container position-fixed top-0 end-0 p-3";
        container.style.zIndex = "1060";
        document.body.appendChild(container);
      }
      const el = document.createElement("div");
      el.className = "toast show";
      el.innerHTML = `
        <div class="toast-header">
          <i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>
          <strong class="me-auto">Error</strong>
          <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">${msg}</div>`;
      container.appendChild(el);
      setTimeout(() => { el.classList.remove("show"); setTimeout(() => el.remove(), 300); }, 5000);
    } catch {
      alert(msg);
    }
  }

  function itemsContainer(zone) { return zone.querySelector(".kanban-items") || zone; }
  function emptyNode(zone) { return zone.querySelector(".kanban-empty"); }
  function countBadge(zone) { return zone.closest(".card")?.querySelector(".kanban-count") || null; }
  function countCards(zone) { return itemsContainer(zone).querySelectorAll(".task-card").length; }
  function updateZoneState(zone) {
    const n = countCards(zone);
    const empty = emptyNode(zone);
    if (empty) empty.classList.toggle("d-none", n > 0);
    const badge = countBadge(zone);
    if (badge) badge.textContent = n;
  }
  function updateAllZones() { document.querySelectorAll(".drop-zone").forEach(updateZoneState); }

  function disableInnerDnD(card) {
    card.querySelectorAll("a, img, button").forEach(el => el.setAttribute("draggable", "false"));
  }

  const DRAGGED_CLASS = "opacity-50";
  const ACTIVE_ZONE_CLASS = "dropzone--active";
  let draggedEl = null;
  let originZone = null;
  let originNextSibling = null;
  let isDropping = false;
  let disabledAnchorStyles = [];

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
    disableInnerDnD(card);

    card.addEventListener("dragstart", onDragStart);
    card.addEventListener("dragend", onDragEnd);
  }
  function attachAllCards() {
    document.querySelectorAll(".task-card").forEach(attachCardHandlers);
  }

  function onDragStart(e) {
    const card = e.currentTarget;
    if (card.dataset.canModify === "0") { e.preventDefault(); return; }

    draggedEl = card;
    draggedEl.classList.add(DRAGGED_CLASS);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", draggedEl.dataset.taskId);

    originZone = draggedEl.closest(".drop-zone");
    originNextSibling = draggedEl.nextElementSibling;

    disabledAnchorStyles = [];
    draggedEl.querySelectorAll("a").forEach(a => {
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
    document.querySelectorAll("." + ACTIVE_ZONE_CLASS).forEach(z => z.classList.remove(ACTIVE_ZONE_CLASS));
  }

  function onDragOver(e) { e.preventDefault(); e.dataTransfer.dropEffect = "move"; }
  function onDragEnter(e, zone) { zone.classList.add(ACTIVE_ZONE_CLASS); }
  function onDragLeave(e, zone) { if (!zone.contains(e.relatedTarget)) zone.classList.remove(ACTIVE_ZONE_CLASS); }

  async function onDrop(e, zone) {
    e.preventDefault();
    if (!draggedEl || isDropping) return;
    zone.classList.remove(ACTIVE_ZONE_CLASS);

    const rawTarget = zone.dataset.status;
    const targetStatus = normalizeStatusKey(rawTarget);  // <-- важно
    const taskId = draggedEl.dataset.taskId;
    const prevStatus = draggedEl.dataset.currentStatus;

    if (!targetStatus) return;
    isDropping = true;

    const targetList = itemsContainer(zone);
    const placeholder = document.createElement("div");
    placeholder.style.height = draggedEl.offsetHeight + "px";
    draggedEl.parentNode.insertBefore(placeholder, draggedEl);
    targetList.appendChild(draggedEl);
    draggedEl.dataset.currentStatus = targetStatus;
    draggedEl.classList.toggle("opacity-75", targetStatus === "done");

    if (originZone) updateZoneState(originZone);
    updateZoneState(zone);

    try {
      const formData = new FormData();
      formData.append("status", targetStatus);
      formData.append("csrfmiddlewaretoken", CSRF);

      const toggleUrl = getToggleUrlFromCard(draggedEl);
      const resp = await fetch(toggleUrl, { method: "POST", body: formData });

      if (!resp.ok) {
        let errMsg = `Server responded ${resp.status}`;
        try {
          const maybeJson = await resp.json();
          if (maybeJson && maybeJson.error) errMsg = maybeJson.error;
        } catch (_) {}
        throw new Error(errMsg);
      }
      let data = null;
      try { data = await resp.json(); } catch (_) {}
      if (!data || data.success !== true) {
        const msg = (data && (data.error || data.detail)) || "Server refused to save the change";
        throw new Error(msg);
      }

      attachCardHandlers(draggedEl);
      updateAllZones();
    } catch (err) {
      if (placeholder && placeholder.parentNode) {
        placeholder.parentNode.insertBefore(draggedEl, placeholder);
      } else if (originZone) {
        const originList = itemsContainer(originZone);
        if (originNextSibling && originNextSibling.parentNode === originList) {
          originList.insertBefore(draggedEl, originNextSibling);
        } else {
          originList.appendChild(draggedEl);
        }
      }
      draggedEl.dataset.currentStatus = prevStatus;
      draggedEl.classList.toggle("opacity-75", prevStatus === "done");
      if (originZone) updateZoneState(originZone);
      updateZoneState(zone);

      toastError("Failed to update status. " + (err?.message || "Please try again."));
    } finally {
      if (placeholder && placeholder.parentNode) placeholder.parentNode.removeChild(placeholder);
      isDropping = false;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    attachAllCards();
    document.querySelectorAll(".drop-zone").forEach(zone => {
      zone.addEventListener("dragover", (e) => onDragOver(e, zone));
      zone.addEventListener("dragenter", (e) => onDragEnter(e, zone));
      zone.addEventListener("dragleave", (e) => onDragLeave(e, zone));
      zone.addEventListener("drop", (e) => onDrop(e, zone));
    });
    updateAllZones();
  });
})();
