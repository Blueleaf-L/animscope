/**
 * Trends — static version
 */
Pages.Trends = {
  render: function () {
    Views.showSkeleton();
    StaticData.load("trends")
      .then(function (data) {
        var html = '<h1 style="margin-bottom:20px;">趋势分析</h1>';
        html += '<div class="card" style="margin-bottom:20px;"><div class="card-title">各类型年度趋势</div><div id="chart-type-trends" class="chart-container" style="height:400px;"></div></div>';
        html += '<div class="card" style="margin-bottom:20px;"><div class="card-title">公司 x 年份 评分热力图</div><div id="chart-heatmap" class="chart-container" style="height:500px;"></div></div>';
        html += '<div id="heatmap-drilldown" class="inline-panel" style="display:none;"></div>';
        Views.setContent(html);

        setTimeout(function () {
          Charts.renderTypeTrendLines("chart-type-trends", data.by_type);
          Charts.renderHeatmap("chart-heatmap", data.heatmap_data, data.companies, data.years);
          document.addEventListener("heatmap-click", function (evt) {
            var cn = evt.detail.companyName, yr = evt.detail.year, p = document.getElementById("heatmap-drilldown");
            if (!p) return;
            StaticData.load("companies_full").then(function (cd) {
              var comp = cd.find(function (c) { return c.name === cn; });
              if (!comp) return;
              var fw = (comp.works||[]).filter(function (w) { return w.year === yr; });
              p.style.display = "";
              p.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;"><h3>' + escapeHtml(cn) + ' - ' + yr + '</h3><button class="btn btn-sm btn-outline" onclick="this.closest(\'.inline-panel\').style.display=\'none\'">关闭</button></div>' + (fw.length ? Views.dataTable([{key:"name",label:"作品"},{key:"rating_label",label:"评级",render:function(v){return Views.ratingBadge(v);}},{key:"rating_score",label:"评分",render:function(v){return v!=null?Analytics.formatScore(v):"-";}}], fw) : "<p>该年份无作品</p>");
            });
          });
        }, 150);
      })
      .catch(function (err) { Views.showError("加载趋势失败", function () { Pages.Trends.render(); }); });
  },
};
