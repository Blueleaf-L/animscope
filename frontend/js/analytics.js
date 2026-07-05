/**
 * Client-side analytics utilities.
 * Only contains logic that CANNOT be done server-side (e.g. browser-specific formatting, client-only filtering).
 * Kept ≤ 50 lines by design — heavy computation lives in the backend.
 */

const Analytics = {
  /**
   * Format a score value for display.
   */
  formatScore(score) {
    if (score == null) return "—";
    const n = Number(score);
    if (n > 0) return "+" + n.toFixed(1);
    return n.toFixed(1);
  },

  /**
   * Truncate text with ellipsis.
   */
  truncate(text, maxLen = 30) {
    if (!text) return "";
    return text.length > maxLen ? text.slice(0, maxLen) + "…" : text;
  },

  /**
   * Parse comma-separated query params from URL hash.
   */
  parseHashParams(hash) {
    const [path, query] = hash.replace("#", "").split("?");
    const params = {};
    if (query) {
      query.split("&").forEach(pair => {
        const [k, v] = pair.split("=");
        params[decodeURIComponent(k)] = decodeURIComponent(v || "");
      });
    }
    return { path, params };
  },

  /**
   * Build hash URL with params.
   */
  buildHash(path, params = {}) {
    const qs = Object.entries(params)
      .filter(([_, v]) => v !== undefined && v !== null && v !== "")
      .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
      .join("&");
    return qs ? `#${path}?${qs}` : `#${path}`;
  },
};
