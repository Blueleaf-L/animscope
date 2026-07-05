/**
 * Global configuration module.
 * Colors are read dynamically from CSS custom properties — never hardcoded.
 */

// Initialize the Pages namespace early (page modules depend on it)
window.Pages = window.Pages || {};

const CONFIG = {
  API_BASE: "/api/v1",
  PAGE_SIZE: 20,
  DEBOUNCE_MS: 200,
  CHART_ANIMATION_DURATION: 500,

  /** Dynamically read colors from CSS variables. Call each time to stay in sync with theme changes. */
  getColors() {
    const s = getComputedStyle(document.documentElement);
    return {
      rating: {
        "年度推荐": s.getPropertyValue("--rating-best").trim(),
        "佳作": s.getPropertyValue("--rating-great").trim(),
        "还行": s.getPropertyValue("--rating-good").trim(),
        "能看": s.getPropertyValue("--rating-ok").trim(),
        "不明": s.getPropertyValue("--rating-unknown").trim(),
        "拉了": s.getPropertyValue("--rating-bad").trim(),
        "史": s.getPropertyValue("--rating-trash").trim(),
      },
      palette: [
        "#5b8def", "#f06b4a", "#3cc9a6", "#7c5ce0", "#f5a623", "#e8405d",
      ],
      textPrimary: s.getPropertyValue("--text-primary").trim(),
      textSecondary: s.getPropertyValue("--text-secondary").trim(),
      bgCard: s.getPropertyValue("--bg-card").trim(),
      borderColor: s.getPropertyValue("--border-color").trim(),
    };
  },

  /** Rating display order */
  RATING_ORDER: ["年度推荐", "佳作", "还行", "能看", "不明", "拉了", "史"],
};

/**
 * Simple HTML escape to prevent XSS on dynamically inserted content.
 */
function escapeHtml(str) {
  if (!str && str !== 0) return "";
  const div = document.createElement("div");
  div.textContent = String(str);
  return div.innerHTML;
}
