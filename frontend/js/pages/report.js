/**
 * Analysis Report — static version
 */
Pages.Report = {
  render: function () {
    Views.showSkeleton();
    try {
      var theme = document.documentElement.getAttribute("data-theme") || "light";
      var html = '<h1 style="margin-bottom:20px;">分析报告</h1>';
      html += '<div class="report-actions"><a href="data/static/charts/heatmap.png" class="btn btn-primary" download>下载图表</a></div>';

      html += '<div class="card" style="margin-bottom:20px;"><div class="card-title">评级体系说明</div><div class="rating-guide">';
      var descs = ["强烈推荐作品", "优秀作品", "中规中矩", "勉强可看", "评价不明", "质量较差", "质量极差"];
      CONFIG.RATING_ORDER.forEach(function (l, i) { html += '<div class="rating-guide-item"><span class="rating-badge rating-' + l + '">' + l + '</span><span style="font-size:0.8rem;color:var(--text-secondary);">' + descs[i] + '</span></div>'; });
      html += '</div></div>';

      html += '<div class="section-grid" style="margin-top:20px;"><div class="card"><div class="card-title">评级分布图</div><img src="data/static/charts/rating_distribution.png" alt="评级分布" style="width:100%;height:auto;" onerror="this.style.display=\'none\'"></div><div class="card"><div class="card-title">评分箱线图</div><img src="data/static/charts/boxplot.png" alt="箱线图" style="width:100%;height:auto;" onerror="this.style.display=\'none\'"></div></div>';
      html += '<div class="card" style="margin-top:20px;"><div class="card-title">公司评分热力图（前20家）</div><img src="data/static/charts/heatmap.png" alt="热力图" style="width:100%;height:auto;" onerror="this.style.display=\'none\'"></div>';

      Views.setContent(html);
    } catch (err) { Views.showError("报告页加载失败", function () { Pages.Report.render(); }); }
  },
};
