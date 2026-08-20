import { getHistory, deleteHistoryItem, clearHistory } from "./api.js";
import { escapeHtml } from "./dom.js";

const PRIORITY_BADGE = {
  critical: "bg-red-500 text-white",
  high:     "bg-orange-400 text-white",
  medium:   "bg-yellow-300 text-yellow-900",
  low:      "bg-gray-200 text-gray-700",
};

const LABEL_COLORS = {
  clear:      "bg-green-100 text-green-800",
  moderate:   "bg-yellow-100 text-yellow-800",
  overloaded: "bg-red-100 text-red-800",
};

let allHistoryItems = [];

function historyRowHtml(item) {
  const p = (item.priority ?? "low").toLowerCase();
  const badge = PRIORITY_BADGE[p] ?? PRIORITY_BADGE.low;
  return `
    <div class="history-row border-b border-slate-100 py-3 last:border-0" data-id="${escapeHtml(item.id)}">
      <div class="flex items-center gap-2 mb-1 cursor-pointer history-row-toggle">
        <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${badge}">${p.toUpperCase()}</span>
        <span class="text-xs text-slate-400">${escapeHtml(item.source)}</span>
        ${item.filtered_out ? `<span class="text-xs text-slate-300 italic">filtered</span>` : ""}
        <span class="text-xs text-slate-300 ml-auto">${new Date(item.processed_at).toLocaleString()}</span>
        <button class="history-delete-btn text-slate-300 hover:text-red-500 text-sm leading-none ml-2" title="Delete this entry">&times;</button>
      </div>
      <p class="text-sm text-slate-700">${escapeHtml(item.summary || item.filter_reason || "(no summary)")}</p>
      <div class="history-row-detail hidden mt-2 text-xs text-slate-600 space-y-1 pl-2 border-l border-slate-100">
        ${item.simplified ? `<p><span class="font-medium">Simplified:</span> ${escapeHtml(item.simplified)}</p>` : ""}
        ${item.filter_reason ? `<p><span class="font-medium">Filter reason:</span> ${escapeHtml(item.filter_reason)}</p>` : ""}
        ${item.suggested_action ? `<p><span class="font-medium">Suggested action:</span> ${escapeHtml(item.suggested_action)}</p>` : ""}
        <p><span class="font-medium">Category:</span> ${escapeHtml(item.category)} · <span class="font-medium">Cognitive cost:</span> ${item.cognitive_cost ?? 0}/10</p>
        <p><span class="font-medium">Received:</span> ${item.received_at ? new Date(item.received_at).toLocaleString() : "—"}</p>
      </div>
    </div>`;
}

function applyFiltersAndRender() {
  const listEl = document.getElementById("history-list");
  const emptyEl = document.getElementById("history-empty");
  const noResultsEl = document.getElementById("history-no-results");
  const controlsEl = document.getElementById("history-controls");
  const clearBtn = document.getElementById("history-clear-btn");

  if (!allHistoryItems.length) {
    emptyEl.classList.remove("hidden");
    noResultsEl.classList.add("hidden");
    listEl.classList.add("hidden");
    controlsEl.classList.add("hidden");
    clearBtn.classList.add("hidden");
    return;
  }

  emptyEl.classList.add("hidden");
  controlsEl.classList.remove("hidden");
  clearBtn.classList.remove("hidden");

  const q = document.getElementById("history-search").value.trim().toLowerCase();
  const priority = document.getElementById("history-priority-filter").value;
  const kept = document.getElementById("history-kept-filter").value;

  const filtered = allHistoryItems.filter(item => {
    if (priority && (item.priority ?? "").toLowerCase() !== priority) return false;
    if (kept === "kept" && item.filtered_out) return false;
    if (kept === "filtered" && !item.filtered_out) return false;
    if (q) {
      const haystack = `${item.source ?? ""} ${item.summary ?? ""} ${item.filter_reason ?? ""}`.toLowerCase();
      if (!haystack.includes(q)) return false;
    }
    return true;
  });

  if (!filtered.length) {
    noResultsEl.classList.remove("hidden");
    listEl.classList.add("hidden");
    return;
  }

  noResultsEl.classList.add("hidden");
  listEl.classList.remove("hidden");
  listEl.innerHTML = filtered.map(historyRowHtml).join("");
}

async function loadHistory() {
  const listEl = document.getElementById("history-list");
  const emptyEl = document.getElementById("history-empty");
  try {
    const { items } = await getHistory(200, 0);
    allHistoryItems = items ?? [];
    applyFiltersAndRender();
  } catch {
    allHistoryItems = [];
    emptyEl.textContent = "Could not load history.";
    emptyEl.classList.remove("hidden");
    listEl.classList.add("hidden");
  }
}

function initHistoryControls() {
  document.getElementById("history-search").addEventListener("input", applyFiltersAndRender);
  document.getElementById("history-priority-filter").addEventListener("change", applyFiltersAndRender);
  document.getElementById("history-kept-filter").addEventListener("change", applyFiltersAndRender);

  document.getElementById("history-clear-btn").addEventListener("click", async () => {
    if (!confirm(`Delete all ${allHistoryItems.length} history entries? This cannot be undone.`)) return;
    try {
      await clearHistory();
      allHistoryItems = [];
      applyFiltersAndRender();
    } catch {
      alert("Could not clear history.");
    }
  });

  document.getElementById("history-list").addEventListener("click", async (e) => {
    const row = e.target.closest(".history-row");
    if (!row) return;
    const id = row.dataset.id;

    if (e.target.closest(".history-delete-btn")) {
      try {
        await deleteHistoryItem(id);
        allHistoryItems = allHistoryItems.filter(item => item.id !== id);
        applyFiltersAndRender();
      } catch {
        alert("Could not delete this entry.");
      }
      return;
    }

    if (e.target.closest(".history-row-toggle")) {
      row.querySelector(".history-row-detail")?.classList.toggle("hidden");
    }
  });
}

export function initInsights() {
  const container = document.getElementById("insights-container");
  const emptyEl = document.getElementById("insights-empty");

  initHistoryControls();
  loadHistory();

  document.addEventListener("batchComplete", e => {
    const { processed, bandwidth, predicted_needs, suggestions } = e.detail ?? {};

    emptyEl.classList.add("hidden");
    container.classList.remove("hidden");
    container.innerHTML = "";

    if (bandwidth) {
      const { score, label, active_items, filtered_items, high_cost_items } = bandwidth;
      const lc = LABEL_COLORS[label] ?? LABEL_COLORS.moderate;
      container.insertAdjacentHTML("beforeend", `
        <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5 mb-4">
          <h3 class="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">Bandwidth Report</h3>
          <div class="flex items-center gap-3 mb-4">
            <span class="text-4xl font-bold text-slate-800">${score}</span>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${lc}">${escapeHtml((label ?? "").toUpperCase())}</span>
          </div>
          <div class="grid grid-cols-3 gap-3 text-center">
            <div class="bg-slate-50 rounded-lg p-2"><div class="text-xl font-bold text-slate-700">${active_items ?? 0}</div><div class="text-xs text-slate-400">Active</div></div>
            <div class="bg-slate-50 rounded-lg p-2"><div class="text-xl font-bold text-slate-700">${filtered_items ?? 0}</div><div class="text-xs text-slate-400">Filtered</div></div>
            <div class="bg-slate-50 rounded-lg p-2"><div class="text-xl font-bold text-slate-700">${(high_cost_items ?? []).length}</div><div class="text-xs text-slate-400">High-cost</div></div>
          </div>
        </div>`);
    }

    if (predicted_needs?.length) {
      const items = predicted_needs.map((n, i) => `<li class="text-sm text-slate-700">${i + 1}. ${escapeHtml(n)}</li>`).join("");
      container.insertAdjacentHTML("beforeend", `
        <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5 mb-4">
          <h3 class="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">Predicted Needs</h3>
          <ul class="space-y-2">${items}</ul>
        </div>`);
    }

    if (suggestions?.length) {
      const items = suggestions.map(s => `<li class="text-sm text-slate-700">• ${escapeHtml(s)}</li>`).join("");
      container.insertAdjacentHTML("beforeend", `
        <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5 mb-4">
          <h3 class="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">Suggestions</h3>
          <ul class="space-y-2">${items}</ul>
        </div>`);
    }

    if (processed?.length) {
      const cards = processed.map(msg => {
        const p = (msg.priority ?? "low").toLowerCase();
        const badge = PRIORITY_BADGE[p] ?? PRIORITY_BADGE.low;
        return `
          <div class="border-b border-slate-100 py-3 last:border-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${badge}">${p.toUpperCase()}</span>
              <span class="text-xs text-slate-400">${escapeHtml(msg.original?.source)}</span>
              ${msg.filtered_out ? `<span class="text-xs text-slate-300 italic">filtered</span>` : ""}
            </div>
            <p class="text-sm text-slate-700">${escapeHtml(msg.summary || msg.original?.content)}</p>
          </div>`;
      }).join("");
      container.insertAdjacentHTML("beforeend", `
        <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
          <details>
            <summary class="text-sm font-semibold text-slate-600 cursor-pointer select-none uppercase tracking-wide">
              Processed Messages (${processed.length})
            </summary>
            <div class="mt-3">${cards}</div>
          </details>
        </div>`);
    }

    // The batch/email fetch that just ran also persisted these rows to
    // storage — refresh History so deletes/filters stay in sync with it.
    loadHistory();
  });
}
