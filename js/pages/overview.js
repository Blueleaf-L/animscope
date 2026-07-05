/**
 * Homepage Overview — static version
 */
Pages.Overview = {
  render: function () {
    Views.showSkeleton();

    StaticData.load("overview")
      .then(function (data) {
        var s = data.stats;
        var html = "";
        html += '<section class="stats-grid">';
        html += Views.statCard(s.total_companies, "动画公司总数", "--color-primary");
        html += Views.statCard(s.total_works, "作品总数", "--color-accent");
        html += Views.statCard(s.avg_score, "行业平均分", "--color-success");
        html += Views.statCard(s.recommended_count, "年度推荐", "--rating-best");
        html += Views.statCard(s.good_count, "佳作+还行", "--rating-great");
        html += Views.statCard(s.trash_count, "翻车作品", "--rating-trash");
        html += '</section>';

        if (data.diagnostics && data.diagnostics.length) {
          html += '<section class="card" style="margin-bottom:20px;">';
          html += '<div class="card-title">行业诊断</div><ul style="padding-left:20px;color:var(--text-secondary);">';
          data.diagnostics.forEach(function (d) {
            html += '<li style="margin-bottom:4px;">' + escapeHtml(d) + '</li>';
          });
          html += '</ul></section>';
        }

        html += '<section class="chart-grid">';
        html += '<div class="card"><div class="card-title">作品评级分布</div>';
        html += '<div id="chart-rating-dist" class="chart-container" style="height:380px;"></div></div>';
        html += '<div class="card"><div class="card-title">公司类型分布</div>';
        html += '<div id="chart-type-rose" class="chart-container" style="height:380px;"></div></div>';
        html += '</section>';
        html += '<section class="card" style="margin-top:20px;">';
        html += '<div class="card-title">年度趋势</div>';
        html += '<div id="chart-yearly-trend" class="chart-container" style="height:380px;"></div>';
        html += '</section>';

        Views.setContent(html);

        setTimeout(function () {
          Charts.renderRingChart("chart-rating-dist", data.rating_distribution);
          Charts.renderRoseChart("chart-type-rose", data.type_distribution);
          Charts.renderDualAxisTrend("chart-yearly-trend", data.yearly_trends);
          var ri = Charts._instances["chart-rating-dist"];
          if (ri) { ri.off("click"); ri.on("click", function (p) { if (p.name === "年度推荐") window.location.hash = "#rankings?tab=recommended"; else if (p.name === "拉了" || p.name === "史") window.location.hash = "#rankings?tab=trash"; else window.location.hash = "#rankings?tab=good"; }); }
          var ro = Charts._instances["chart-type-rose"];
          if (ro) { ro.off("click"); ro.on("click", function (p) { if (p.name) window.location.hash = "#companies?type=" + encodeURIComponent(p.name); }); }
        }, 150);
      })
      .catch(function (err) {
        console.error("Overview:", err);
        Views.showError("加载首页失败", function () { Pages.Overview.render(); });
      });
  },
};
