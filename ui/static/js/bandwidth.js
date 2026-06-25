import { processBatch, uuid } from "./api.js";

const SCORE_CLASSES = {
  clear:      { ring: "ring-green-400",  text: "text-green-600",  badge: "bg-green-100 text-green-800" },
  moderate:   { ring: "ring-yellow-400", text: "text-yellow-600", badge: "bg-yellow-100 text-yellow-800" },
  overloaded: { ring: "ring-red-500",    text: "text-red-600",    badge: "bg-red-100 text-red-800" },
};

function updateScoreDisplay(bandwidth) {
  const { score, label, active_items, filtered_items, high_cost_items } = bandwidth;
  const cls = SCORE_CLASSES[label] ?? SCORE_CLASSES.moderate;

  const scoreEl = document.getElementById("bandwidth-score");
  scoreEl.textContent = score;
  scoreEl.className = `text-5xl font-bold ${cls.text}`;

  const ringEl = document.getElementById("bandwidth-ring");
  Object.values(SCORE_CLASSES).forEach(c => ringEl.classList.remove(c.ring));
  ringEl.classList.remove("ring-gray-200");
  ringEl.classList.add(cls.ring);

  const labelEl = document.getElementById("bandwidth-label");
  labelEl.textContent = label.toUpperCase();
  labelEl.className = `inline-block px-3 py-1 rounded-full text-sm font-semibold mt-2 ${cls.badge}`;

  document.getElementById("stat-active").textContent = active_items ?? 0;
  document.getElementById("stat-filtered").textContent = filtered_items ?? 0;
  document.getElementById("stat-highcost").textContent = (high_cost_items ?? []).length;
}

export function initBandwidth() {
  document.addEventListener("bandwidthUpdate", e => updateScoreDisplay(e.detail));

  const modal = document.getElementById("batch-modal");
  const openBtn = document.getElementById("open-batch-btn");
  const cancelBtns = document.querySelectorAll(".batch-cancel-btn");
  const processBtn = document.getElementById("batch-process");
  const textarea = document.getElementById("batch-input");
  const errorEl = document.getElementById("batch-error");
  const timerEl = document.getElementById("batch-timer");

  openBtn.addEventListener("click", () => {
    modal.classList.remove("hidden");
    textarea.focus();
  });

  cancelBtns.forEach(btn => btn.addEventListener("click", () => modal.classList.add("hidden")));

  modal.addEventListener("click", e => {
    if (e.target === modal) modal.classList.add("hidden");
  });

  processBtn.addEventListener("click", async () => {
    errorEl.classList.add("hidden");
    const raw = textarea.value.trim();
    if (!raw) {
      errorEl.textContent = "Please enter at least one message.";
      errorEl.classList.remove("hidden");
      return;
    }

    let messages;
    try {
      const parsed = JSON.parse(raw);
      messages = Array.isArray(parsed) ? parsed : [parsed];
    } catch {
      messages = raw
        .split("\n")
        .map(l => l.trim())
        .filter(Boolean)
        .map(content => ({
          id: uuid(),
          source: "manual",
          content,
          category: "information",
          received_at: new Date().toISOString(),
          metadata: {},
        }));
    }

    if (messages.length === 0) {
      errorEl.textContent = "No valid messages found.";
      errorEl.classList.remove("hidden");
      return;
    }

    processBtn.disabled = true;
    processBtn.textContent = "Processing...";
    let elapsed = 0;
    timerEl.textContent = "0s";
    timerEl.classList.remove("hidden");
    const interval = setInterval(() => { elapsed++; timerEl.textContent = `${elapsed}s`; }, 1000);

    try {
      const result = await processBatch(messages);
      clearInterval(interval);
      modal.classList.add("hidden");
      timerEl.classList.add("hidden");
      textarea.value = "";

      if (result.bandwidth) updateScoreDisplay(result.bandwidth);

      document.dispatchEvent(new CustomEvent("batchComplete", { detail: result }));

      const count = result.processed?.length ?? 0;
      if (count > 0) {
        const badge = document.getElementById("insights-badge");
        badge.textContent = count;
        badge.classList.remove("hidden");
      }
    } catch (err) {
      clearInterval(interval);
      timerEl.classList.add("hidden");
      errorEl.textContent = err.message ?? "Processing failed.";
      errorEl.classList.remove("hidden");
    } finally {
      processBtn.disabled = false;
      processBtn.textContent = "Process Batch";
    }
  });
}