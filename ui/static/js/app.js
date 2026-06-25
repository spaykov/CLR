import { health } from "./api.js";
import { initBandwidth } from "./bandwidth.js";
import { initInbox } from "./inbox.js";
import { initEmail } from "./email.js";
import { initNotifications } from "./notifications.js";
import { initDecisions } from "./decisions.js";
import { initTools } from "./tools.js";
import { initInsights } from "./insights.js";

const TABS = ["bandwidth", "inbox", "email", "notifications", "decisions", "tools", "insights"];

export function activateTab(name) {
  TABS.forEach(t => {
    document.getElementById(`panel-${t}`).classList.toggle("hidden", t !== name);
    const btn = document.querySelector(`[data-tab="${t}"]`);
    if (t === name) {
      btn.classList.add("border-b-2", "border-blue-600", "text-blue-600");
      btn.classList.remove("text-slate-500");
    } else {
      btn.classList.remove("border-b-2", "border-blue-600", "text-blue-600");
      btn.classList.add("text-slate-500");
    }
    btn.setAttribute("aria-selected", t === name ? "true" : "false");
  });
  if (name === "insights") {
    document.getElementById("insights-badge").classList.add("hidden");
  }
}

document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => activateTab(btn.dataset.tab));
});

health()
  .then(data => {
    const dot = document.getElementById("health-indicator");
    const txt = document.getElementById("health-text");
    const ok = data.status === "ok";
    dot.classList.replace("bg-gray-300", ok ? "bg-green-400" : "bg-red-500");
    dot.title = ok ? "Backend online" : "Backend offline";
    txt.textContent = ok ? "Online" : "Offline";
    txt.className = ok ? "text-xs text-green-600" : "text-xs text-red-500";
  })
  .catch(() => {
    const dot = document.getElementById("health-indicator");
    const txt = document.getElementById("health-text");
    dot.classList.replace("bg-gray-300", "bg-red-500");
    dot.title = "Backend offline";
    txt.textContent = "Offline";
    txt.className = "text-xs text-red-500";
  });

initBandwidth();
initInbox();
initEmail();
initNotifications();
initDecisions();
initTools();
initInsights();

activateTab("bandwidth");