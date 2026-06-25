const BASE_URL = "/api/v1";

async function getEmailStatus() {
  const res = await fetch(BASE_URL + "/email/status");
  return res.json();
}

async function fetchEmails(limit) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 300000);
  try {
    const res = await fetch(BASE_URL + "/email/fetch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ limit }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ?? "Fetch failed");
    }
    return res.json();
  } catch (e) {
    clearTimeout(timer);
    if (e.name === "AbortError") throw new Error("Request timed out");
    throw e;
  }
}

function showConnected() {
  document.getElementById("email-connect-section").classList.add("hidden");
  document.getElementById("email-fetch-section").classList.remove("hidden");
}

function showDisconnected() {
  document.getElementById("email-connect-section").classList.remove("hidden");
  document.getElementById("email-fetch-section").classList.add("hidden");
}

export function initEmail() {
  getEmailStatus().then(data => {
    if (data.configured) showConnected();
    else showDisconnected();
  }).catch(() => showDisconnected());

  // Recheck button
  document.getElementById("email-connect-btn").addEventListener("click", async () => {
    const btn = document.getElementById("email-connect-btn");
    const errorEl = document.getElementById("email-error");
    errorEl.classList.add("hidden");
    btn.disabled = true;
    btn.textContent = "Checking...";
    try {
      const { configured } = await getEmailStatus();
      if (configured) {
        showConnected();
      } else {
        errorEl.innerHTML = `
          <p class="font-medium">Not configured yet.</p>
          <p class="text-xs mt-1">Set CLR_GMAIL_ADDRESS in .env, then run python main.py from a terminal and enter the app password when prompted, then check again.</p>`;
        errorEl.classList.remove("hidden");
      }
    } catch (err) {
      errorEl.textContent = err.message ?? "Could not check email status.";
      errorEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
      btn.textContent = "Check Connection";
    }
  });

  // Fetch button
  document.getElementById("email-fetch-btn").addEventListener("click", async () => {
    const btn = document.getElementById("email-fetch-btn");
    const errorEl = document.getElementById("email-error");
    const statusEl = document.getElementById("email-status");
    const timerEl = document.getElementById("email-timer");
    errorEl.classList.add("hidden");
    statusEl.classList.add("hidden");

    const limit = parseInt(document.getElementById("email-limit").value, 10) || 10;

    btn.disabled = true;
    btn.innerHTML = spinner("Fetching...");
    let elapsed = 0;
    timerEl.textContent = "0s";
    timerEl.classList.remove("hidden");
    const interval = setInterval(() => { elapsed++; timerEl.textContent = `${elapsed}s`; }, 1000);

    try {
      const result = await fetchEmails(limit);
      clearInterval(interval);
      timerEl.classList.add("hidden");

      const count = result.fetched ?? result.processed?.length ?? 0;
      statusEl.textContent = `✓ Fetched and processed ${count} email${count !== 1 ? "s" : ""} — check Dashboard and Insights.`;
      statusEl.classList.remove("hidden");

      if (result.bandwidth) {
        document.dispatchEvent(new CustomEvent("bandwidthUpdate", { detail: result.bandwidth }));
      }
      document.dispatchEvent(new CustomEvent("batchComplete", { detail: result }));

      if (count > 0) {
        const badge = document.getElementById("insights-badge");
        badge.textContent = count;
        badge.classList.remove("hidden");
      }

      btn.textContent = "Fetch Again";
    } catch (err) {
      clearInterval(interval);
      timerEl.classList.add("hidden");
      errorEl.textContent = err.message ?? "Email fetch failed.";
      errorEl.classList.remove("hidden");
      btn.textContent = "Fetch Emails";
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