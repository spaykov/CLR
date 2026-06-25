import { rewriteText, summarizeText } from "./api.js";

function setupTool({ inputId, btnId, outputId, copyBtnId, errorId, apiFn, btnLabel }) {
  const input = document.getElementById(inputId);
  const btn = document.getElementById(btnId);
  const output = document.getElementById(outputId);
  const copyBtn = document.getElementById(copyBtnId);
  const errorEl = document.getElementById(errorId);

  btn.addEventListener("click", async () => {
    errorEl.classList.add("hidden");
    const text = input.value.trim();
    if (!text) {
      errorEl.textContent = "Please enter some text.";
      errorEl.classList.remove("hidden");
      return;
    }

    btn.disabled = true;
    btn.innerHTML = spinner("Working...");
    output.textContent = "";
    copyBtn.classList.add("hidden");

    try {
      const data = await apiFn(text);
      output.textContent = data.result ?? "";
      copyBtn.classList.remove("hidden");
      btn.textContent = "Done ✓";
      setTimeout(() => { btn.textContent = btnLabel; }, 1500);
    } catch (err) {
      errorEl.textContent = err.message ?? "Failed.";
      errorEl.classList.remove("hidden");
      btn.textContent = btnLabel;
    } finally {
      btn.disabled = false;
    }
  });

  copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(output.textContent).then(() => {
      copyBtn.textContent = "Copied!";
      setTimeout(() => { copyBtn.textContent = "Copy"; }, 1500);
    });
  });
}

export function initTools() {
  setupTool({
    inputId: "rewrite-input",
    btnId: "rewrite-btn",
    outputId: "rewrite-output",
    copyBtnId: "rewrite-copy",
    errorId: "rewrite-error",
    apiFn: rewriteText,
    btnLabel: "Simplify",
  });

  setupTool({
    inputId: "summarize-input",
    btnId: "summarize-btn",
    outputId: "summarize-output",
    copyBtnId: "summarize-copy",
    errorId: "summarize-error",
    apiFn: summarizeText,
    btnLabel: "Summarize",
  });
}

function spinner(label) {
  return `<svg class="animate-spin h-4 w-4 inline mr-1" viewBox="0 0 24 24" fill="none">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
  </svg>${label}`;
}