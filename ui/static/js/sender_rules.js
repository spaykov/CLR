import { getSenderRules, addSenderRule, deleteSenderRule } from "./api.js";
import { escapeHtml } from "./dom.js";

const ACTION_BADGE = {
  ignore: "bg-gray-200 text-gray-700",
  digest: "bg-blue-100 text-blue-800",
};

function rowHtml(rule) {
  const badge = ACTION_BADGE[rule.action] ?? ACTION_BADGE.digest;
  return `
    <div class="flex items-center gap-2 py-2 border-b border-slate-100 last:border-0" data-id="${rule.id}">
      <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${badge}">${escapeHtml(rule.action.toUpperCase())}</span>
      <span class="text-sm text-slate-700 flex-1 truncate">${escapeHtml(rule.pattern)}</span>
      <button class="sender-rule-delete-btn text-slate-300 hover:text-red-500 text-sm leading-none" title="Delete this rule">&times;</button>
    </div>`;
}

async function loadRules() {
  const listEl = document.getElementById("sender-rule-list");
  const emptyEl = document.getElementById("sender-rule-empty");
  try {
    const { items } = await getSenderRules();
    if (!items?.length) {
      emptyEl.classList.remove("hidden");
      listEl.innerHTML = "";
      return;
    }
    emptyEl.classList.add("hidden");
    listEl.innerHTML = items.map(rowHtml).join("");
  } catch {
    emptyEl.textContent = "Could not load sender rules.";
    emptyEl.classList.remove("hidden");
  }
}

export function initSenderRules() {
  const form = document.getElementById("sender-rule-form");
  const btn = document.getElementById("sender-rule-submit");
  const errorEl = document.getElementById("sender-rule-error");
  const patternInput = document.getElementById("sender-rule-pattern");
  const actionSelect = document.getElementById("sender-rule-action");
  const listEl = document.getElementById("sender-rule-list");

  loadRules();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("hidden");
    const pattern = patternInput.value.trim();
    if (!pattern) {
      errorEl.textContent = "Enter a sender pattern (e.g. an email address or domain).";
      errorEl.classList.remove("hidden");
      return;
    }

    btn.disabled = true;
    try {
      await addSenderRule(pattern, actionSelect.value);
      patternInput.value = "";
      await loadRules();
    } catch (err) {
      errorEl.textContent = err.message ?? "Could not add rule.";
      errorEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
    }
  });

  listEl.addEventListener("click", async (e) => {
    const delBtn = e.target.closest(".sender-rule-delete-btn");
    if (!delBtn) return;
    const row = e.target.closest("[data-id]");
    const id = row.dataset.id;
    delBtn.disabled = true;
    try {
      await deleteSenderRule(id);
      await loadRules();
    } catch {
      delBtn.disabled = false;
    }
  });
}
