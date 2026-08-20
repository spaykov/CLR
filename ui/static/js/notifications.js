import { filterNotification, uuid } from "./api.js";
import { escapeHtml } from "./dom.js";

const STORAGE_KEY = "clr_notification_results";
const MAX_HISTORY = 10;

function renderCard(result) {
  const kept = result.kept;
  const borderCls = kept ? "border-green-400" : "border-red-400";
  const badgeCls = kept
    ? "bg-green-100 text-green-800 border border-green-300"
    : "bg-red-100 text-red-800 border border-red-300";
  const icon = kept ? "✓ KEPT" : "✗ BLOCKED";
  const titleText = kept && result.simplified_title
    ? result.simplified_title
    : result.original?.title ?? "";
  const titleClass = kept ? "text-slate-800" : "text-slate-400 line-through";

  return `
    <div class="bg-white rounded-xl border-l-4 ${borderCls} shadow-sm p-4 mb-3">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${badgeCls}">${icon}</span>
        <span class="text-sm text-slate-400">${escapeHtml(result.original?.app ?? "—")}</span>
      </div>
      <p class="text-sm font-medium ${titleClass} mb-1">${escapeHtml(titleText)}</p>
      ${kept && result.simplified_body ? `<p class="text-sm text-slate-600 mb-1">${escapeHtml(result.simplified_body)}</p>` : ""}
      <p class="text-xs text-slate-400 italic mt-1">${escapeHtml(result.reason ?? "")}</p>
    </div>`;
}

function saveResult(result) {
  const list = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? "[]");
  list.unshift(result);
  if (list.length > MAX_HISTORY) list.length = MAX_HISTORY;
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

export function initNotifications() {
  const form = document.getElementById("notif-form");
  const btn = document.getElementById("notif-submit");
  const errorEl = document.getElementById("notif-error");
  const resultsEl = document.getElementById("notif-results");
  const emptyEl = document.getElementById("notif-empty");

  const history = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? "[]");
  if (history.length > 0) {
    emptyEl.classList.add("hidden");
    history.forEach(r => resultsEl.insertAdjacentHTML("beforeend", renderCard(r)));
  }

  form.addEventListener("submit", async e => {
    e.preventDefault();
    errorEl.classList.add("hidden");

    const app = document.getElementById("notif-app").value.trim();
    const title = document.getElementById("notif-title").value.trim();
    const body = document.getElementById("notif-body").value.trim();
    const is_urgent = document.getElementById("notif-urgent").checked;

    if (!app || !title) {
      errorEl.textContent = "App name and title are required.";
      errorEl.classList.remove("hidden");
      return;
    }

    const notification = {
      id: uuid(),
      app,
      title,
      body,
      received_at: new Date().toISOString(),
      is_urgent,
    };

    btn.disabled = true;
    const origText = btn.textContent;
    btn.innerHTML = spinner("Filtering...");

    try {
      const result = await filterNotification(notification);
      saveResult(result);
      emptyEl.classList.add("hidden");
      resultsEl.insertAdjacentHTML("afterbegin", renderCard(result));
      btn.textContent = "Done ✓";
      setTimeout(() => { btn.textContent = origText; }, 1500);
    } catch (err) {
      errorEl.textContent = err.message ?? "Filtering failed.";
      errorEl.classList.remove("hidden");
      btn.textContent = origText;
    } finally {
      btn.disabled = false;
    }
  });
}

function spinner(label) {
  return `<svg class="animate-spin h-4 w-4 inline mr-1" viewBox="0 0 24 24" fill="none">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
  </svg>${label}`;
}