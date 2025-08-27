(function () {
  "use strict";

  function getCsrfToken() {
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    if (input) return input.value;
    const m = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  function detectAppPrefix() {
    const path = window.location.pathname;
    const m = path.match(/^(.*?\/app\/)/);
    if (m) return m[1];
    return path.endsWith("/") ? path : path.replace(/[^/]+$/, "");
  }

  function getToggleUrl(taskId, sourceEl) {
    if (sourceEl && sourceEl.dataset && sourceEl.dataset.url) {
      return sourceEl.dataset.url;
    }
    const card =
      document.querySelector(`[data-task-id="${taskId}"]`) || null;
    if (card && card.dataset && card.dataset.toggleUrl) {
      return card.dataset.toggleUrl;
    }
    const base = detectAppPrefix();
    const sep = base.endsWith("/") ? "" : "/";
    return `${base}${sep}task/${taskId}/toggle-status/`;
  }

  function ensureToastContainer() {
    let c = document.querySelector(".toast-container");
    if (!c) {
      c = document.createElement("div");
      c.className = "toast-container position-fixed top-0 end-0 p-3";
      c.style.zIndex = "1060";
      document.body.appendChild(c);
    }
    return c;
  }

  function showStatusToast(newStatus) {
    const toastContainer = ensureToastContainer();
    const toastId = "status-toast-" + Date.now();
    const toast = document.createElement("div");
    toast.id = toastId;
    toast.className = "toast show";
    toast.setAttribute("role", "alert");
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
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
      }
    }, 4000);
  }

  function showErrorToast(message) {
    const toastContainer = ensureToastContainer();
    const toastId = "error-toast-" + Date.now();
    const toast = document.createElement("div");
    toast.id = toastId;
    toast.className = "toast show";
    toast.innerHTML = `
      <div class="toast-header">
        <i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>
        <strong class="me-auto">Error</strong>
        <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
      </div>
      <div class="toast-body">${message}</div>
    `;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      if (document.getElementById(toastId)) {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
      }
    }, 5000);
  }

  function updateTaskUI(taskId, data) {
    const statusSpan = document.getElementById("status-" + taskId);

    const icons = { todo: "⏱", in_progress: "🔄", review: "👁️", done: "✓" };
    const colors = {
      todo: "text-warning",
      in_progress: "text-info",
      review: "text-primary",
      done: "text-success",
    };

    if (statusSpan) {
      const card = statusSpan.closest(".task-card");
      if (card) card.classList.add("status-updating");

      setTimeout(() => {
        statusSpan.innerHTML = `<span class="${
          colors[data.status_key]
        } fw-bold">${icons[data.status_key]} ${data.new_status}</span>`;

        if (card) {
          card.classList.remove(
            "border-warning",
            "border-info",
            "border-primary",
            "border-success",
            "opacity-75",
            "status-updating"
          );

          const borderClasses = {
            todo: "border-warning",
            in_progress: "border-info",
            review: "border-primary",
            done: "border-success",
          };
          card.classList.add(borderClasses[data.status_key]);
          if (data.status_key === "done") card.classList.add("opacity-75");
        }
      }, 200);
    }

    const alertBox = document.getElementById("task-status-alert");
    if (alertBox) updateStatusAlert(alertBox, data);
  }

  function updateStatusAlert(statusAlert, data) {
    statusAlert.classList.add("status-updating");

    setTimeout(() => {
      const alertClasses = {
        todo: "alert-warning",
        in_progress: "alert-info",
        review: "alert-primary",
        done: "alert-success",
      };
      const iconClasses = {
        todo: "bi-clock",
        in_progress: "bi-arrow-clockwise",
        review: "bi-eye",
        done: "bi-check-circle",
      };

      statusAlert.className = `alert ${alertClasses[data.status_key]}`;
      statusAlert.innerHTML = `
        <i class="${iconClasses[data.status_key]}"></i>
        Status: ${data.new_status}
      `;

      statusAlert.classList.remove("status-updating");
      statusAlert.classList.add("status-updated");
      setTimeout(() => statusAlert.classList.remove("status-updated"), 600);
    }, 300);
  }

  function insertOptionInOrder(dropdown, newLi, status) {
    const statusOrder = ["todo", "in_progress", "review", "done"];
    const statusIndex = statusOrder.indexOf(status);

    const existingOptions = dropdown.querySelectorAll(".status-option");
    let inserted = false;

    for (let option of existingOptions) {
      const optionStatus = option.getAttribute("data-status");
      const optionIndex = statusOrder.indexOf(optionStatus);
      if (statusIndex < optionIndex) {
        option.closest("li").parentElement.insertBefore(newLi, option.closest("li"));
        inserted = true;
        break;
      }
    }
    if (!inserted) dropdown.appendChild(newLi);
  }

  function updateDropdownOptions(taskId, oldStatus, newStatus) {
    const statusOptions = document.querySelectorAll(
      `[data-task-id="${taskId}"].status-option`
    );
    if (!statusOptions.length) return;

    const dropdown = statusOptions[0].closest(".dropdown-menu");
    if (!dropdown) return;

    const statusData = {
      todo: { label: "To Do" },
      in_progress: { label: "In Progress" },
      review: { label: "Review" },
      done: { label: "Done" },
    };

    const newStatusOption = dropdown.querySelector(
      `[data-task-id="${taskId}"][data-status="${newStatus}"]`
    );
    if (newStatusOption) newStatusOption.closest("li").remove();

    if (
      oldStatus &&
      !dropdown.querySelector(
        `[data-task-id="${taskId}"][data-status="${oldStatus}"]`
      )
    ) {
      const li = document.createElement("li");
      const statusInfo = statusData[oldStatus];
      li.innerHTML = `
        <button class="dropdown-item status-option"
                data-task-id="${taskId}"
                data-status="${oldStatus}">
          ${statusInfo.label}
        </button>
      `;
      insertOptionInOrder(dropdown, li, oldStatus);
    }
  }

  async function handleStatusChange(e) {
    e.preventDefault();

    const btn = this;
    const taskId = btn.getAttribute("data-task-id");
    const newStatus = btn.getAttribute("data-status");

    const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
    const currentStatus = taskCard ? taskCard.getAttribute("data-current-status") : null;

    const url = getToggleUrl(taskId, btn);
    if (!url) {
      showErrorToast("Toggle URL not found");
      return;
    }

    const formData = new FormData();
    formData.append("status", newStatus);
    formData.append("csrfmiddlewaretoken", getCsrfToken());

    try {
      const response = await fetch(url, { method: "POST", body: formData });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!data.success) throw new Error(data.error || "Unknown error");

      updateTaskUI(taskId, data);
      updateDropdownOptions(taskId, currentStatus, data.status_key);
      if (taskCard) taskCard.setAttribute("data-current-status", data.status_key);
      showStatusToast(data.new_status);
    } catch (err) {
      showErrorToast("Failed to update status. Please try again.");
    }
  }

  document.addEventListener("click", function (e) {
    const opt = e.target.closest(".status-option");
    if (opt) handleStatusChange.call(opt, e);
  });
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".status-option").forEach((el) => {
      el.addEventListener("click", function (e) {
        e.preventDefault();
      });
    });
  });
})();
