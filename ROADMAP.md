# Roadmap

Ideas that are worth doing but aren't scheduled yet.

## Emergency contact alert for critical action items

When a message is filtered as `critical` priority (e.g. the physical-safety
backstop in `clr/core/safety.py` fires, or a future rule flags something
that truly can't wait), send a text message to a designated emergency
contact rather than relying on the user to have the dashboard open.

Open questions to resolve when this gets picked up:
- SMS provider (Twilio, etc.) and where the contact number/credentials live
  (`.env`, same pattern as other secrets)
- What counts as "critical enough to text" vs. just high-priority in-app
- Rate limiting / de-duplication so a burst of similar alerts doesn't spam
  the contact
