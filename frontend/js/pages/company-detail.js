/**
 * Company Detail — #company/:id
 */
Pages.CompanyDetail = {
  render: function (opts) {
    Views.showSkeleton();
    var companyId = (opts && opts.params) ? opts.params.id : null;
    if (!companyId) {
      Views.showError("缺少公司ID", function () { Router.navigate("companies"); });
      return;
    }
    var highlightTrash = (opts && opts.query && opts.query.highlight === "trash");

    API.get("/companies/" + companyId)
      .then(function (data) {
        var works = data.works || [];
        works.sort(function (a, b) { return (b.year || 0) - (a.year || 0); });

        var scores = [];
        var recCount = 0, trashCount = 0;
        for (var i = 0; i < works.length; i++) {
          var w = works[i];
          if (w.rating_score != null) scores.push(w.rating_score);
          if (w.rating_label === "年度推荐") recCount++;
          if (w.rating_label === "拉了" || w.rating_label === "史") trashCount++;
        }

        var years = [];
        for (var j = 0; j < works.length; j++) {
          if (works[j].year) years.push(works[j].year);
        }
        years.sort(function (a, b) { return a - b; });
        var minYear = years[0] || 2000;
        var maxYear = years[years.length - 1] || 2025;

        var theme = document.documentElement.getAttribute("data-theme") || "light";

        var html = '<div class="company-hero"><div>';
        html += '<h1>' + escapeHtml(data.name) + ' ' + Views.typeTag(data.type) + '</h1>';
        html += '<div class="company-meta" style="margin-top:8px;">';
        html += '<span>' + works.length + ' 部作品</span>';
        html += '<span>均分 ' + (data.avg_score != null ? Analytics.formatScore(data.avg_score) : "-") + '</span>';
        html += '<span>推荐 ' + recCount + '</span>';
        html += '<span style="color:var(--color-danger)">翻车 ' + trashCount + '</span>';
        html += '</div></div>';
        html += '<div><img src="' + CONFIG.API_BASE + '/charts/company-radar?id=' + companyId + '&theme=' + theme + '" alt="雷达图" style="max-width:300px;height:auto;" onerror="this.style.display=\'none\'"></div>';
        html += '</div>';

        html += '<div class="card" style="margin-bottom:20px;">';
        html += '<div class="card-title">作品时间线</div>';
        if (Charts.isMobile()) {
          html += '<div style="max-height:400px;overflow-y:auto;">';
          for (var k = 0; k < works.length; k++) {
            html += '<div style="padding:8px;border-bottom:1px solid var(--border-color);display:flex;justify-content:space-between;">';
            html += '<span>' + escapeHtml(works[k].name) + '</span>';
            html += '<span>' + (works[k].year || "-") + ' ' + Views.ratingBadge(works[k].rating_label) + '</span></div>';
          }
          html += '</div>';
        } else {
          html += '<div id="chart-timeline" class="chart-container" style="height:380px;"></div>';
        }
        html += '</div>';

        html += '<div class="filter-bar">';
        html += '<label>年份:</label><span>' + minYear + '</span>';
        html += '<div class="time-slider" style="flex:1;margin:0 12px;">';
        html += '<input type="range" id="year-slider" min="' + minYear + '" max="' + maxYear + '" value="' + maxYear + '" style="width:100%;"></div>';
        html += '<span id="slider-year-label">全部</span>';
        html += '<select id="rating-filter"><option value="">全部评级</option>';
        CONFIG.RATING_ORDER.forEach(function (r) {
          html += '<option value="' + r + '">' + r + '</option>';
        });
        html += '</select></div>';
        html += '<div id="works-table"></div>';

        Views.setContent(html);

        if (!Charts.isMobile()) {
          setTimeout(function () { Charts.renderTimeline("chart-timeline", works); }, 150);
        }

        renderWorksTable(works);

        var slider = document.getElementById("year-slider");
        var sliderLabel = document.getElementById("slider-year-label");
        var ratingFilter = document.getElementById("rating-filter");

        function filterWorks() {
          var maxY = parseInt(slider.value) || maxYear;
          sliderLabel.textContent = maxY >= maxYear ? "全部" : ("≤ " + maxY);
          var rating = ratingFilter.value || "";
          var filtered = works.filter(function (w) {
            if (maxY < maxYear && w.year && w.year > maxY) return false;
            if (rating && w.rating_label !== rating) return false;
            return true;
          });
          renderWorksTable(filtered);
        }

        function renderWorksTable(list) {
          var cols = [
            { key: "name", label: "作品名称" },
            { key: "year", label: "年份", render: function (v) { return v || "-"; } },
            { key: "rating_label", label: "评级", render: function (v) { return Views.ratingBadge(v); } },
            { key: "rating_score", label: "评分", render: function (v) { return v != null ? Analytics.formatScore(v) : "-"; } },
          ];
          var tbl = document.getElementById("works-table");
          if (tbl) tbl.innerHTML = Views.dataTable(cols, list, { emptyText: "暂无作品" });
        }

        if (slider) slider.oninput = filterWorks;
        if (ratingFilter) ratingFilter.onchange = filterWorks;

        if (highlightTrash) {
          setTimeout(function () {
            var rows = document.querySelectorAll(".data-table tbody tr");
            for (var r = 0; r < rows.length; r++) {
              var cells = rows[r].querySelectorAll("td");
              for (var c = 0; c < cells.length; c++) {
                if (cells[c].textContent === "拉了" || cells[c].textContent === "史") {
                  rows[r].style.background = "rgba(232,64,93,0.1)";
                  rows[r].scrollIntoView({ behavior: "smooth", block: "center" });
                  break;
                }
              }
            }
          }, 300);
        }
      })
      .catch(function (err) {
        console.error("Company detail error:", err);
        Views.showError(err.message || "加载公司详情失败", function () {
          Pages.CompanyDetail.render(opts);
        });
      });
  },
};
