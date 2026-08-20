import { processMessage, uuid } from "./api.js";
import { escapeHtml } from "./dom.js";

const STORAGE_KEY = "clr_inbox_results";
const MAX_HISTORY = 20;

const PRIORITY = {
  critical: { border: "border-red-500",   badge: "bg-red-500 text-white" },
  high:     { border: "border-orange-400", badge: "bg-orange-400 text-white" },
  medium:   { border: "border-yellow-300", badge: "bg-yellow-300 text-yellow-900" },
  low:      { border: "border-gray-200",   badge: "bg-gray-200 text-gray-700" },
};

function costDots(cost) {
  const n = Math.round(Math.min(Math.max(cost ?? 0, 0), 10));
  return Array.from({ length: 10 }, (_, i) =>
    `<span class="inline-block w-2 h-2 rounded-full mx-0.5 ${i < n ? "bg-orange-400" : "bg-slate-200"}"></span>`
  ).join("");
}

function renderCard(msg) {
  const p = (msg.priority ?? "low").toLowerCase();
  const cls = PRIORITY[p] ?? PRIORITY.low;
  const filtered = msg.filtered_out;
  const dim = filtered ? "opacity-60" : "";
  const strike = filtered ? "line-through text-slate-400" : "";

  return `
    <div class="bg-white rounded-xl border-l-4 ${cls.border} shadow-sm p-4 mb-3 ${dim}">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${cls.badge}">${p.toUpperCase()}</span>
          <span class="text-sm text-slate-500 ${strike}">${escapeHtml(msg.original?.source ?? "—")} · ${escapeHtml(msg.original?.category ?? "—")}</span>
        </div>
        <div class="flex gap-0.5 flex-shrink-0 ml-2">${costDots(msg.cognitive_cost)}</div>
      </div>
      ${msg.summary ? `<p class="text-sm font-medium text-slate-800 mb-1 ${strike}"><span class="text-slate-400 text-xs mr-1">Summary</span>${escapeHtml(msg.summary)}</p>` : ""}
      ${msg.simplified ? `<p class="text-sm text-slate-600 mb-2"><span class="text-slate-400 text-xs mr-1">Simplified</span>${escapeHtml(msg.simplified)}</p>` : ""}
      ${filtered ? `<p class="text-xs text-slate-400 italic">Filtered: ${escapeHtml(msg.filter_reason ?? "")}</p>` : ""}
      <details class="mt-2">
        <summary class="text-xs text-slate-400 cursor-pointer select-none hover:text-slate-600">Details</summary>
        <div class="mt-2 text-xs text-slate-600 space-y-1 pl-2 border-l border-slate-100">
          ${msg.filter_reason ? `<p><span class="font-medium">Filter reason:</span> ${escapeHtml(msg.filter_reason)}</p>` : ""}
          ${msg.action_required ? `<p><span class="font-medium">Action required:</span> yes</p>` : ""}
          ${msg.suggested_action ? `<p><span class="font-medium">Suggested:</span> ${escapeHtml(msg.suggested_action)}</p>` : ""}
          <p class="text-slate-400 break-words"><span class="font-medium text-slate-500">Original:</span> ${escapeHtml(msg.original?.content ?? "")}</p>
        </div>
      </details>
    </div>`;
}

function saveResult(result) {
  const list = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? "[]");
  list.unshift(result);
  if (list.length > MAX_HISTORY) list.length = MAX_HISTORY;
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

export function initInbox() {
  const form = document.getElementById("inbox-form");
  const btn = document.getElementById("inbox-submit");
  const errorEl = document.getElementById("inbox-error");
  const resultsEl = document.getElementById("inbox-results");
  const emptyEl = document.getElementById("inbox-empty");

  const history = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? "[]");
  if (history.length > 0) {
    emptyEl.classList.add("hidden");
    history.forEach(r => resultsEl.insertAdjacentHTML("beforeend", renderCard(r)));
  }

  form.addEventListener("submit", async e => {
    e.preventDefault();
    errorEl.classList.add("hidden");

    const source = document.getElementById("inbox-source").value.trim();
    const category = document.getElementById("inbox-category").value;
    const content = document.getElementById("inbox-content").value.trim();
    const metaRaw = document.getElementById("inbox-metadata").value.trim();

    if (!source || !content) {
      errorEl.textContent = "Source and content are required.";
      errorEl.classList.remove("hidden");
      return;
    }

    let metadata = {};
    if (metaRaw) {
      try { metadata = JSON.parse(metaRaw); }
      catch { errorEl.textContent = "Metadata must be valid JSON."; errorEl.classList.remove("hidden"); return; }
    }

    const message = { id: uuid(), source, category, content, received_at: new Date().toISOString(), metadata };

    btn.disabled = true;
    const origText = btn.textContent;
    btn.innerHTML = spinner("Processing...");

    try {
      const result = await processMessage(message);
      saveResult(result);
      emptyEl.classList.add("hidden");
      resultsEl.insertAdjacentHTML("afterbegin", renderCard(result));
      btn.textContent = "Done ✓";
      setTimeout(() => { btn.textContent = origText; }, 1500);
    } catch (err) {
      errorEl.textContent = err.message ?? "Processing failed.";
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