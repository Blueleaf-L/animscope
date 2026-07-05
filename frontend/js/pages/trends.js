/**
 * Trends Analysis — #trends
 */
Pages.Trends = {
  render: function () {
    Views.showSkeleton();

    API.get("/analysis/trends")
      .then(function (data) {
        var html = '<h1 style="margin-bottom:20px;">趋势分析</h1>';
        html += '<div class="card" style="margin-bottom:20px;">';
        html += '<div class="card-title">各类型年度趋势对比</div>';
        html += '<div id="chart-type-trends" class="chart-container" style="height:400px;"></div></div>';
        html += '<div class="card" style="margin-bottom:20px;">';
        html += '<div class="card-title">公司 x 年份 评分热力图 <span style="font-weight:400;font-size:0.85rem;color:var(--text-muted);">（点击格子查看详情）</span></div>';
        html += '<div id="chart-heatmap" class="chart-container" style="height:500px;"></div></div>';
        html += '<div id="heatmap-drilldown" class="inline-panel" style="display:none;"></div>';

        Views.setContent(html);

        setTimeout(function () {
          Charts.renderTypeTrendLines("chart-type-trends", data.by_type);
          Charts.renderHeatmap("chart-heatmap", data.heatmap_data, data.companies, data.years);

          document.addEventListener("heatmap-click", function (evt) {
            var companyName = evt.detail.companyName;
            var year = evt.detail.year;
            var panel = document.getElementById("heatmap-drilldown");
            if (!panel) return;

            API.get("/companies?q=" + encodeURIComponent(companyName) + "&size=1")
              .then(function (compData) {
                if (!compData.items.length) return;
                var cid = compData.items[0].id;
                return API.get("/companies/" + cid + "/works?year_min=" + year + "&year_max=" + year);
              })
              .then(function (worksData) {
                if (!worksData) return;
                var works = worksData.items || [];
                panel.style.display = "";
                var ph = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">';
                ph += '<h3>' + escapeHtml(companyName) + ' — ' + year + ' 年作品</h3>';
                ph += '<button class="btn btn-sm btn-outline" onclick="this.closest(\'.inline-panel\').style.display=\'none\'">关闭</button></div>';
                if (works.length) {
                  ph += Views.dataTable([
                    { key: "name", label: "作品名称" },
                    { key: "rating_label", label: "评级", render: function (v) { return Views.ratingBadge(v); } },
                    { key: "rating_score", label: "评分", render: function (v) { return v != null ? Analytics.formatScore(v) : "-"; } },
                  ], works);
                } else {
                  ph += "<p>该年份无作品数据</p>";
                }
                panel.innerHTML = ph;
              })
              .catch(function () {
                panel.style.display = "none";
              });
          });
        }, 150);
      })
      .catch(function (err) {
        console.error("Trends error:", err);
        Views.showError(err.message || "加载趋势数据失败", function () {
          Pages.Trends.render();
        });
      });
  },
};
