import { getSenderRules, addSenderRule, updateSenderRule, deleteSenderRule } from "./api.js";
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
      <button class="sender-rule-edit-btn text-xs text-blue-600 hover:text-blue-800 font-medium px-2 py-1">Edit</button>
      <button class="sender-rule-delete-btn text-xs text-red-500 hover:text-red-700 font-medium px-2 py-1">Delete</button>
    </div>`;
}

let rules = [];
let editingId = null;

function setEditMode(rule) {
  editingId = rule?.id ?? null;
  const submitBtn = document.getElementById("sender-rule-submit");
  const cancelBtn = document.getElementById("sender-rule-cancel-edit");
  const patternInput = document.getElementById("sender-rule-pattern");
  const actionSelect = document.getElementById("sender-rule-action");

  if (rule) {
    patternInput.value = rule.pattern;
    actionSelect.value = rule.action;
    submitBtn.textContent = "Save Changes";
    cancelBtn.classList.remove("hidden");
    patternInput.focus();
  } else {
    patternInput.value = "";
    actionSelect.value = "digest";
    submitBtn.textContent = "Add";
    cancelBtn.classList.add("hidden");
  }
}

async function loadRules() {
  const listEl = document.getElementById("sender-rule-list");
  const emptyEl = document.getElementById("sender-rule-empty");
  try {
    const { items } = await getSenderRules();
    rules = items ?? [];
    if (!rules.length) {
      emptyEl.classList.remove("hidden");
      listEl.innerHTML = "";
      return;
    }
    emptyEl.classList.add("hidden");
    listEl.innerHTML = rules.map(rowHtml).join("");
  } catch {
    emptyEl.textContent = "Could not load sender rules.";
    emptyEl.classList.remove("hidden");
  }
}

export function initSenderRules() {
  const form = document.getElementById("sender-rule-form");
  const btn = document.getElementById("sender-rule-submit");
  const cancelBtn = document.getElementById("sender-rule-cancel-edit");
  const errorEl = document.getElementById("sender-rule-error");
  const patternInput = document.getElementById("sender-rule-pattern");
  const actionSelect = document.getElementById("sender-rule-action");
  const listEl = document.getElementById("sender-rule-list");

  loadRules();

  cancelBtn.addEventListener("click", () => setEditMode(null));

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
      if (editingId != null) {
        await updateSenderRule(editingId, pattern, actionSelect.value);
      } else {
        await addSenderRule(pattern, actionSelect.value);
      }
      setEditMode(null);
      await loadRules();
    } catch (err) {
      errorEl.textContent = err.message ?? "Could not save rule.";
      errorEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
    }
  });

  listEl.addEventListener("click", async (e) => {
    const row = e.target.closest("[data-id]");
    if (!row) return;
    const id = row.dataset.id;

    if (e.target.closest(".sender-rule-edit-btn")) {
      const rule = rules.find(r => String(r.id) === String(id));
      if (rule) setEditMode(rule);
      return;
    }

    const delBtn = e.target.closest(".sender-rule-delete-btn");
    if (delBtn) {
      delBtn.disabled = true;
      try {
        await deleteSenderRule(id);
        if (String(editingId) === String(id)) setEditMode(null);
        await loadRules();
      } catch {
        delBtn.disabled = false;
      }
    }
  });
}
