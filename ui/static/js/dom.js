// Shared by any module that interpolates message/notification content into
// innerHTML. That content ultimately comes from real email/notification
// text — attacker-reachable (anyone who emails or notifies the user) — so it
// must never be inserted unescaped.
export function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}
