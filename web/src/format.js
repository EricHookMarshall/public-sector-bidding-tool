// Shared display formatters. These were copy-pasted across the stage screens
// (fmtMoney ×3, deadlineBadge ×3, daysUntil ×2) and had drifted — Complete hard-
// coded its urgency thresholds while Plan/Manage read `imminent_days` from the
// server. One home so "urgent" means the same thing everywhere.

// A number → GBP-style currency, or "—" for blank/non-numeric. `currency`
// defaults to GBP but Search passes the notice's own currency. The try/catch
// guards against an invalid ISO currency code from source data.
export function fmtMoney(n, currency = "GBP") {
  if (n === null || n === undefined || n === "" || Number.isNaN(Number(n))) return "—";
  try {
    return new Intl.NumberFormat("en-GB", {
      style: "currency", currency: currency || "GBP", maximumFractionDigits: 0,
    }).format(Number(n));
  } catch {
    return `${currency || ""} ${n}`;
  }
}

// A days-to-deadline count → short label + urgency class (drives colour).
// `imminent` is the "urgent" window (server's `imminent_days`, default 7); at or
// inside it is critical, within 2× is a warning. null days → no badge.
export function deadlineBadge(days, imminent = 7) {
  if (days === null || days === undefined) return null;
  if (days < 0) return { label: `${Math.abs(days)}d late`, cls: "crit" };
  if (days <= imminent) return { label: `${days}d left`, cls: "crit" };
  if (days <= imminent * 2) return { label: `${days}d`, cls: "warn" };
  return { label: `${days}d`, cls: "ok" };
}

// An ISO date string → a short "12 Jan 2026" label, "—" for blank, or the raw
// string if it doesn't parse. Was copy-pasted identically in Search + Triage.
export function fmtDate(s) {
  if (!s) return "—";
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? s : d.toLocaleDateString("en-GB", {
    year: "numeric", month: "short", day: "numeric",
  });
}

// Whole days from today (local midnight) until an ISO date, or null if blank/
// unparseable. Used by the detail views, which read raw dates from the form (the
// boards send pre-computed day counts).
export function daysUntil(value) {
  if (!value) return null;
  const d = new Date(String(value).slice(0, 10));
  if (Number.isNaN(d.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((d - today) / 86400000);
}
