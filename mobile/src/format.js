// Small pure helpers (no React), so they can be tested with `npm test`.

const EAT_OFFSET_MS = 3 * 60 * 60 * 1000; // East Africa Time is UTC+3, with no daylight saving
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const pad = (n) => String(n).padStart(2, '0');

// "2026-11-04T16:49:01Z" -> "04 Nov 2026, 19:49" (Nairobi time)
function formatEAT(iso) {
  if (!iso) return '';
  const date = new Date(new Date(iso).getTime() + EAT_OFFSET_MS);
  if (Number.isNaN(date.getTime())) return '';
  return `${pad(date.getUTCDate())} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}, `
    + `${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}`;
}

// "5 min ago", "3 h ago", "2 days ago"
function timeAgo(iso, now = Date.now()) {
  if (!iso) return '';
  const seconds = Math.max(0, Math.round((now - new Date(iso).getTime()) / 1000));
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.floor(hours / 24);
  return days === 1 ? '1 day ago' : `${days} days ago`;
}

// The API returns errors like { phone_number: ["..."], password2: ["..."] }.
// This picks the first message, for showing in a single banner.
function firstError(errors) {
  if (!errors) return '';
  const first = Object.values(errors)[0];
  return Array.isArray(first) ? first[0] : String(first || '');
}

// Maps the API's field names to the field names used on the sign-up screen.
function mapRegisterErrors(errors) {
  const mapped = {};
  Object.entries(errors || {}).forEach(([key, messages]) => {
    const field = { password1: 'password', password2: 'password', __all__: 'form' }[key] || key;
    if (!mapped[field]) mapped[field] = Array.isArray(messages) ? messages[0] : String(messages);
  });
  return mapped;
}

module.exports = { formatEAT, timeAgo, firstError, mapRegisterErrors };
