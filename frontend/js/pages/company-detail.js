/**
 * Company Detail — static version
 */
Pages.CompanyDetail = {
  render: function (opts) {
    Views.showSkeleton();
    var companyId = parseInt((opts && opts.params) ? opts.params.id : null);
    if (!companyId) { Views.showError("缺少公司ID", function () { Router.navigate("companies"); }); return; }

    StaticData.findCompany(companyId)
      .then(function (data) {
        var works = (data.works || []).slice().sort(function (a, b) { return (b.year || 0) - (a.year || 0); });
        var recCount = 0, trashCount = 0, scores = [], years = [];
        works.forEach(function (w) {
          if (w.rating_score != null) scores.push(w.rating_score);
          if (w.rating_label === "年度推荐") recCount++;
          if (w.rating_label === "拉了" || w.rating_label === "史") trashCount++;
          if (w.year) years.push(w.year);
        });
        years.sort(function (a, b) { return a - b; });
        var minYear = years[0] || 2010, maxYear = years[years.length - 1] || 2026;

        var html = '<div class="company-hero"><div><h1>' + escapeHtml(data.name) + ' ' + Views.typeTag(data.type) + '</h1>';
        html += '<div class="company-meta" style="margin-top:8px;">';
        html += '<span>' + works.length + ' 部作品</span><span>均分 ' + (data.avg_score != null ? Analytics.formatScore(data.avg_score) : "-") + '</span>';
        html += '<span>推荐 ' + recCount + '</span><span style="color:var(--color-danger)">翻车 ' + trashCount + '</span></div></div></div>';

        // Radar chart (ECharts version)
        html += '<div class="card" style="margin-bottom:20px;"><div class="card-title">综合雷达图</div>';
        html += '<div id="chart-radar" class="chart-container" style="height:380px;"></div></div>';

        html += '<div class="card" style="margin-bottom:20px;"><div class="card-title">作品时间线</div>';
        if (Charts.isMobile()) {
          html += '<div style="max-height:400px;overflow-y:auto;">';
          works.forEach(function (w) { html += '<div style="padding:8px;border-bottom:1px solid var(--border-color);display:flex;justify-content:space-between;"><span>' + escapeHtml(w.name) + '</span><span>' + (w.year||"-") + ' ' + Views.ratingBadge(w.rating_label) + '</span></div>'; });
          html += '</div>';
        } else { html += '<div id="chart-timeline" class="chart-container" style="height:380px;"></div>'; }
        html += '</div>';

        html += '<div class="filter-bar"><label>年份:</label><span>' + minYear + '</span><div class="time-slider" style="flex:1;margin:0 12px;"><input type="range" id="year-slider" min="' + minYear + '" max="' + maxYear + '" value="' + maxYear + '" style="width:100%;"></div><span id="slider-year-label">全部</span>';
        html += '<select id="rating-filter"><option value="">全部评级</option>';
        CONFIG.RATING_ORDER.forEach(function (r) { html += '<option value="' + r + '">' + r + '</option>'; });
        html += '</select></div><div id="works-table"></div>';

        Views.setContent(html);

        // Charts
        if (!Charts.isMobile()) setTimeout(function () { Charts.renderTimeline("chart-timeline", works); }, 150);
        setTimeout(function () { renderRadarChart(data, works); }, 200);

        // Table
        renderTable(works);
        var slider = document.getElementById("year-slider"), sLabel = document.getElementById("slider-year-label"), rFilter = document.getElementById("rating-filter");
        function doFilter() {
          var maxY = parseInt(slider.value) || maxYear;
          sLabel.textContent = maxY >= maxYear ? "全部" : ("<= " + maxY);
          var rating = rFilter.value || "";
          var f = works.filter(function (w) { if (maxY < maxYear && w.year && w.year > maxY) return false; if (rating && w.rating_label !== rating) return false; return true; });
          renderTable(f);
        }
        if (slider) slider.oninput = doFilter;
        if (rFilter) rFilter.onchange = doFilter;
      })
      .catch(function (err) { Views.showError("加载公司详情失败", function () { Pages.CompanyDetail.render(opts); }); });
  },
};

function renderRadarChart(data, works) {
  var colors = CONFIG.getColors();
  var inst = Charts._getInstance("chart-radar"); if (!inst) return;
  var scores = []; works.forEach(function (w) { if (w.rating_score != null) scores.push(w.rating_score); });
  var avg = scores.length ? scores.reduce(function (a,b) { return a+b; }, 0) / scores.length : 0;
  var recR = works.length ? works.filter(function(w){return w.rating_label==="年度推荐"}).length / works.length : 0;
  var trashR = works.length ? works.filter(function(w){return w.rating_label==="拉了"||w.rating_label==="史"}).length / works.length : 0;
  var goodR = works.length ? works.filter(function(w){return w.rating_label==="佳作"||w.rating_label==="还行"}).length / works.length : 0;
  var mx = scores.length ? Math.max.apply(null, scores) : 0, mn = scores.length ? Math.min.apply(null, scores) : 0;
  var rng = mx - mn || 1;

  inst.setOption({
    radar: { indicator: [{name:"平均分",max:1},{name:"作品数",max:1},{name:"推荐率",max:1},{name:"良品率",max:1},{name:"稳定性",max:1},{name:"最高分",max:1}] },
    series: [{ type: "radar", data: [{ value: [(avg+2)/8, Math.min(works.length/30,1), recR, goodR, works.length>1?1-Math.min(0.5,0.3):0.3, (mx+2)/8], name: data.name, areaStyle: { color: colors.palette[0], opacity: 0.2 } }] }],
  }, true);
}

function renderTable(list) {
  var cols = [{ key: "name", label: "作品名称" }, { key: "year", label: "年份", render: function(v){return v||"-";} }, { key: "rating_label", label: "评级", render: function(v){return Views.ratingBadge(v);} }, { key: "rating_score", label: "评分", render: function(v){return v!=null?Analytics.formatScore(v):"-";} }];
  var t = document.getElementById("works-table"); if (t) t.innerHTML = Views.dataTable(cols, list, { emptyText: "暂无作品" });
}
