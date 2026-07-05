/**
 * Analysis Report — #report
 */
Pages.Report = {
  render: function () {
    Views.showSkeleton();

    try {
      var theme = document.documentElement.getAttribute("data-theme") || "light";

      var html = '';
      html += '<h1 style="margin-bottom:20px;">分析报告</h1>';
      html += '<div class="report-actions">';
      html += '<a href="' + CONFIG.API_BASE + '/charts/report?format=pdf" class="btn btn-primary" download>下载 PDF 分析报告</a>';
      html += '<button class="btn btn-outline" id="refresh-dashboard">刷新仪表盘</button>';
      html += '</div>';

      html += '<div class="card" style="margin-bottom:20px;">';
      html += '<div class="card-title">行业仪表盘（Plotly 交互式）</div>';
      html += '<div id="plotly-dashboard" class="dashboard-frame" style="min-height:600px;">';
      html += '<div style="text-align:center;padding:60px;color:var(--text-muted);">正在加载仪表盘...</div>';
      html += '</div></div>';

      html += '<div class="card" style="margin-bottom:20px;">';
      html += '<div class="card-title">评级体系说明</div>';
      html += '<div class="rating-guide">';

      var labels = CONFIG.RATING_ORDER;
      var descriptions = ["强烈推荐作品", "优秀作品", "中规中矩", "勉强可看", "评价不明", "质量较差", "质量极差"];

      for (var i = 0; i < labels.length; i++) {
        html += '<div class="rating-guide-item">';
        html += '<span class="rating-badge rating-' + labels[i] + '">' + labels[i] + '</span>';
        html += '<span style="font-size:0.8rem;color:var(--text-secondary);">' + descriptions[i] + '</span>';
        html += '</div>';
      }

      html += '</div></div>';

      html += '<div class="section-grid" style="margin-top:20px;">';
      html += '<div class="card"><div class="card-title">评级分布图</div>';
      html += '<img src="' + CONFIG.API_BASE + '/charts/rating-distribution?theme=' + theme + '" alt="评级分布" style="width:100%;height:auto;" onerror="this.style.display=\'none\'"></div>';
      html += '<div class="card"><div class="card-title">评分箱线图</div>';
      html += '<img src="' + CONFIG.API_BASE + '/charts/boxplot?theme=' + theme + '" alt="箱线图" style="width:100%;height:auto;" onerror="this.style.display=\'none\'"></div>';
      html += '</div>';

      html += '<div class="card" style="margin-top:20px;">';
      html += '<div class="card-title">公司评分热力图（前20家）</div>';
      html += '<img src="' + CONFIG.API_BASE + '/charts/heatmap?top_n=20&theme=' + theme + '" alt="热力图" style="width:100%;height:auto;" onerror="this.style.display=\'none\'"></div>';

      Views.setContent(html);

      Pages.Report._loadDashboard();

      var refreshBtn = document.getElementById("refresh-dashboard");
      if (refreshBtn) {
        refreshBtn.onclick = function () { Pages.Report._loadDashboard(); };
      }
    } catch (err) {
      console.error("Report render error:", err);
      Views.showError("报告页加载失败: " + (err.message || "未知错误"), function () { Pages.Report.render(); });
    }
  },

  _loadDashboard: function () {
    var container = document.getElementById("plotly-dashboard");
    if (!container) return;

    container.innerHTML = '<div style="text-align:center;padding:60px;color:var(--text-muted);">正在加载仪表盘...</div>';

    fetch(CONFIG.API_BASE + "/charts/industry-dashboard")
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.text();
      })
      .then(function (text) {
        container.innerHTML = text;
      })
      .catch(function (err) {
        container.innerHTML = '<div class="error-state"><p>仪表盘加载失败: ' + escapeHtml(err.message) + '</p></div>';
      });
  },
};
