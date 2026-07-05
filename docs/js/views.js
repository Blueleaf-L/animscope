/**
 * DOM rendering utilities — shared across pages.
 */

const Views = {
  /**
   * Render a stat card.
   */
  statCard(value, label, colorVar = "--color-primary") {
    return `
      <div class="stat-card">
        <div class="stat-value" style="color: var(${colorVar})">${escapeHtml(String(value))}</div>
        <div class="stat-label">${escapeHtml(label)}</div>
      </div>
    `;
  },

  /**
   * Render a rating badge.
   */
  ratingBadge(label) {
    if (!label) return '<span class="tag">—</span>';
    return `<span class="rating-badge rating-${label}">${escapeHtml(label)}</span>`;
  },

  /**
   * Render a company type tag.
   */
  typeTag(type) {
    const cls = type === "2D" ? "tag-2D" : type === "3D" ? "tag-3D" : "tag-hybrid";
    return `<span class="tag ${cls}">${escapeHtml(type)}</span>`;
  },

  /**
   * Render a clickable company name link.
   */
  companyLink(id, name) {
    return `<a href="#company/${id}" class="company-link">${escapeHtml(name)}</a>`;
  },

  /**
   * Render a data table from column definitions and row data.
   * @param {Array} columns — [{ key, label, render?, className? }]
   * @param {Array} rows — array of data objects
   * @param {object} opts — { rowClick, emptyText }
   */
  dataTable(columns, rows, opts = {}) {
    if (!rows.length) {
      return `<div class="error-state"><p>${opts.emptyText || "暂无数据"}</p></div>`;
    }

    const headerHtml = columns.map(c =>
      `<th class="${c.className || ''}">${escapeHtml(c.label)}</th>`
    ).join("");

    const bodyHtml = rows.map((row, i) => {
      const cells = columns.map(c => {
        const val = row[c.key];
        const content = c.render ? c.render(val, row) : escapeHtml(val ?? "—");
        return `<td>${content}</td>`;
      }).join("");
      const clickAttr = opts.rowClick ? ` data-index="${i}" class="clickable-row"` : "";
      return `<tr${clickAttr}>${cells}</tr>`;
    }).join("");

    return `
      <div class="table-wrapper">
        <table class="data-table">
          <thead><tr>${headerHtml}</tr></thead>
          <tbody>${bodyHtml}</tbody>
        </table>
      </div>
    `;
  },

  /**
   * Show skeleton loading.
   */
  showSkeleton() {
    const sk = document.getElementById("skeleton");
    const pc = document.getElementById("page-content");
    const es = document.getElementById("error-state");
    if (sk) sk.style.display = "";
    if (pc) pc.style.display = "none";
    if (es) es.style.display = "none";
  },

  /**
   * Show page content.
   */
  showContent() {
    const sk = document.getElementById("skeleton");
    const pc = document.getElementById("page-content");
    const es = document.getElementById("error-state");
    if (sk) sk.style.display = "none";
    if (pc) pc.style.display = "";
    if (es) es.style.display = "none";
  },

  /**
   * Show error state.
   */
  showError(message, onRetry) {
    const sk = document.getElementById("skeleton");
    const pc = document.getElementById("page-content");
    const es = document.getElementById("error-state");
    if (sk) sk.style.display = "none";
    if (pc) pc.style.display = "none";
    if (es) es.style.display = "";
    const msgEl = document.getElementById("error-message");
    if (msgEl) msgEl.textContent = message || "未知错误";
    const btn = document.getElementById("retry-btn");
    if (btn && onRetry) {
      btn.onclick = onRetry;
    }
  },

  /**
   * Set page content HTML safely.
   */
  setContent(html) {
    const pc = document.getElementById("page-content");
    if (pc) pc.innerHTML = html;
    this.showContent();
  },

  /**
   * Debounce utility.
   */
  debounce(fn, ms) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), ms);
    };
  },
};
