import { getPriorityList, acknowledgeItem } from "./api.js";
import { escapeHtml } from "./dom.js";

const PRIORITY_BADGE = {
  critical: "bg-red-500 text-white",
  high:     "bg-orange-400 text-white",
  medium:   "bg-yellow-300 text-yellow-900",
  low:      "bg-gray-200 text-gray-700",
};

const REFRESH_INTERVAL_MS = 60000;

function rowHtml(item) {
  const p = (item.priority ?? "low").toLowerCase();
  const badge = PRIORITY_BADGE[p] ?? PRIORITY_BADGE.low;
  const receivedAt = item.received_at ? new Date(item.received_at).toLocaleString() : "—";
  return `
    <div class="priority-row border-b border-slate-100 py-3 last:border-0" data-id="${escapeHtml(item.id)}">
      <div class="flex items-center gap-2 mb-1">
        <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${badge}">${p.toUpperCase()}</span>
        <span class="text-xs text-slate-400">${escapeHtml(item.source)}</span>
        <span class="text-xs text-slate-300 ml-auto" title="Time the message itself was sent/received">${receivedAt}</span>
      </div>
      <p class="text-sm text-slate-700 mb-2">${escapeHtml(item.summary || item.filter_reason || "(no summary)")}</p>
      <button class="priority-ack-btn text-xs text-blue-600 hover:text-blue-800 font-medium">Acknowledge</button>
    </div>`;
}

async function loadPriorityList() {
  const listEl = document.getElementById("priority-list");
  const emptyEl = document.getElementById("priority-empty");
  try {
    const { items } = await getPriorityList(20);
    if (!items?.length) {
      emptyEl.classList.remove("hidden");
      listEl.innerHTML = "";
      return;
    }
    emptyEl.classList.add("hidden");
    listEl.innerHTML = items.map(rowHtml).join("");
  } catch {
    // Leave whatever was already shown rather than clearing it on a transient error.
  }
}

export function initPriority() {
  loadPriorityList();
  setInterval(loadPriorityList, REFRESH_INTERVAL_MS);
  document.addEventListener("batchComplete", loadPriorityList);

  document.getElementById("priority-list").addEventListener("click", async (e) => {
    const btn = e.target.closest(".priority-ack-btn");
    if (!btn) return;
    const row = e.target.closest(".priority-row");
    const id = row.dataset.id;
    btn.disabled = true;
    try {
      await acknowledgeItem(id);
      row.remove();
      if (!document.getElementById("priority-list").children.length) {
        document.getElementById("priority-empty").classList.remove("hidden");
      }
    } catch {
      btn.disabled = false;
    }
  });
}
