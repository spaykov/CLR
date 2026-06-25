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

export function initInsights() {
  const container = document.getElementById("insights-container");
  const emptyEl = document.getElementById("insights-empty");

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
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${lc}">${(label ?? "").toUpperCase()}</span>
          </div>
          <div class="grid grid-cols-3 gap-3 text-center">
            <div class="bg-slate-50 rounded-lg p-2"><div class="text-xl font-bold text-slate-700">${active_items ?? 0}</div><div class="text-xs text-slate-400">Active</div></div>
            <div class="bg-slate-50 rounded-lg p-2"><div class="text-xl font-bold text-slate-700">${filtered_items ?? 0}</div><div class="text-xs text-slate-400">Filtered</div></div>
            <div class="bg-slate-50 rounded-lg p-2"><div class="text-xl font-bold text-slate-700">${(high_cost_items ?? []).length}</div><div class="text-xs text-slate-400">High-cost</div></div>
          </div>
        </div>`);
    }

    if (predicted_needs?.length) {
      const items = predicted_needs.map((n, i) => `<li class="text-sm text-slate-700">${i + 1}. ${n}</li>`).join("");
      container.insertAdjacentHTML("beforeend", `
        <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5 mb-4">
          <h3 class="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">Predicted Needs</h3>
          <ul class="space-y-2">${items}</ul>
        </div>`);
    }

    if (suggestions?.length) {
      const items = suggestions.map(s => `<li class="text-sm text-slate-700">• ${s}</li>`).join("");
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
              <span class="text-xs text-slate-400">${msg.original?.source ?? ""}</span>
              ${msg.filtered_out ? `<span class="text-xs text-slate-300 italic">filtered</span>` : ""}
            </div>
            <p class="text-sm text-slate-700">${msg.summary ?? msg.original?.content ?? ""}</p>
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
  });
}