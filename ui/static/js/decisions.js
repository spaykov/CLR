import { decide, uuid } from "./api.js";

function renderResult(task) {
  if (task.auto_decided) {
    const conf = Math.round((task.confidence ?? 0) * 100);
    return `
      <div class="bg-white rounded-xl border border-green-300 shadow-sm p-5">
        <div class="flex items-center gap-2 mb-3">
          <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-green-100 text-green-800 border border-green-300">✓ Auto-decided</span>
        </div>
        <p class="text-sm font-medium text-slate-800 mb-4">${task.decision ?? ""}</p>
        <div class="mb-3">
          <div class="flex justify-between text-xs text-slate-500 mb-1">
            <span>Confidence</span><span>${conf}%</span>
          </div>
          <div class="bg-gray-200 rounded-full h-2">
            <div class="bg-blue-500 h-2 rounded-full transition-all" style="width: ${conf}%"></div>
          </div>
        </div>
        <p class="text-xs text-slate-500 italic">${task.reasoning ?? ""}</p>
      </div>`;
  }
  return `
    <div class="bg-white rounded-xl border border-yellow-300 shadow-sm p-5">
      <div class="flex items-center gap-2 mb-3">
        <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-800 border border-yellow-300">⚠ Needs your input</span>
      </div>
      <p class="text-xs text-slate-600 italic">${task.reasoning ?? "This decision requires your judgement."}</p>
    </div>`;
}

function makeOptionRow(index, removable) {
  const row = document.createElement("div");
  row.className = "flex gap-2";
  const removeDisabled = removable ? "" : "disabled";
  const removeColor = removable ? "text-slate-400 hover:text-red-500" : "text-slate-200 cursor-not-allowed";
  row.innerHTML = `
    <input type="text" placeholder="Option ${index + 1}"
      class="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400" />
    <button type="button" ${removeDisabled} class="remove-option ${removeColor} px-2 text-xl leading-none">−</button>`;
  row.querySelector(".remove-option").addEventListener("click", () => {
    const container = document.getElementById("options-container");
    if (container.children.length > 2) row.remove();
  });
  return row;
}

export function initDecisions() {
  const form = document.getElementById("decision-form");
  const btn = document.getElementById("decision-submit");
  const errorEl = document.getElementById("decision-error");
  const resultEl = document.getElementById("decision-result");
  const addOptionBtn = document.getElementById("add-option");
  const container = document.getElementById("options-container");

  container.appendChild(makeOptionRow(0, false));
  container.appendChild(makeOptionRow(1, false));

  addOptionBtn.addEventListener("click", () => {
    const idx = container.children.length;
    const row = makeOptionRow(idx, true);
    container.appendChild(row);
    if (container.children.length > 2) {
      Array.from(container.querySelectorAll(".remove-option")).forEach(b => {
        b.disabled = false;
        b.className = "remove-option text-slate-400 hover:text-red-500 px-2 text-xl leading-none";
      });
    }
  });

  form.addEventListener("submit", async e => {
    e.preventDefault();
    errorEl.classList.add("hidden");
    resultEl.innerHTML = "";

    const question = document.getElementById("decision-question").value.trim();
    const context = document.getElementById("decision-context").value.trim();
    const options = Array.from(container.querySelectorAll("input"))
      .map(i => i.value.trim())
      .filter(Boolean);

    if (!question) {
      errorEl.textContent = "Question is required.";
      errorEl.classList.remove("hidden");
      return;
    }
    if (options.length < 2) {
      errorEl.textContent = "At least 2 options are required.";
      errorEl.classList.remove("hidden");
      return;
    }

    const task = {
      id: uuid(),
      question,
      options,
      context,
      auto_decided: false,
      decision: null,
      confidence: null,
      reasoning: null,
    };

    btn.disabled = true;
    const origText = btn.textContent;
    btn.innerHTML = spinner("Deciding...");

    try {
      const result = await decide(task);
      resultEl.innerHTML = renderResult(result);
      btn.textContent = "Done ✓";
      setTimeout(() => { btn.textContent = origText; }, 1500);
    } catch (err) {
      errorEl.textContent = err.message ?? "Decision failed.";
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