/**
 * Company Comparison — #compare
 */
Pages.Compare = {
  _selectedIds: [],

  render: function (opts) {
    var self = this;
    Views.showSkeleton();

    if (opts && opts.query && opts.query.ids) {
      self._selectedIds = opts.query.ids.split(",").map(Number).filter(Boolean);
    }

    API.get("/companies?size=100&sort=name")
      .then(function (companiesData) {
        var allCompanies = companiesData.items;

        var html = '<h1 style="margin-bottom:20px;">公司对比</h1>';
        html += '<div class="card" style="margin-bottom:20px;">';
        html += '<div class="card-title">选择对比公司（2-4家）</div>';
        html += '<p style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:12px;">点击公司名称选择或取消，最多4家</p>';
        html += '<div class="compare-selector" id="compare-selector">';

        for (var i = 0; i < allCompanies.length; i++) {
          var c = allCompanies[i];
          var sel = self._selectedIds.indexOf(c.id) >= 0;
          html += '<span class="compare-chip' + (sel ? " selected" : "") + '" data-id="' + c.id + '">';
          if (sel) html += '<span class="remove">X</span>';
          html += escapeHtml(c.name) + '</span>';
        }

        html += '</div>';
        html += '<button class="btn btn-primary" id="compare-btn"' + (self._selectedIds.length < 2 ? " disabled" : "") + '>';
        html += '对比选中公司（' + self._selectedIds.length + '家）</button>';
        html += '</div>';
        html += '<div id="compare-results"></div>';

        Views.setContent(html);

        var chips = document.querySelectorAll(".compare-chip");
        for (var j = 0; j < chips.length; j++) {
          chips[j].onclick = function () {
            var id = parseInt(this.dataset.id);
            var idx = self._selectedIds.indexOf(id);
            if (idx >= 0) {
              self._selectedIds.splice(idx, 1);
            } else if (self._selectedIds.length < 4) {
              self._selectedIds.push(id);
            } else {
              showToast("最多选择4家公司", "error");
              return;
            }
            Pages.Compare.render({ query: { ids: self._selectedIds.join(",") } });
          };
        }

        var compareBtn = document.getElementById("compare-btn");
        if (compareBtn) {
          compareBtn.onclick = function () {
            if (self._selectedIds.length >= 2) {
              Router.navigate(Analytics.buildHash("compare", { ids: self._selectedIds.join(",") }));
            }
          };
        }

        if (self._selectedIds.length >= 2) {
          self._loadComparison();
        }
      })
      .catch(function (err) {
        console.error("Compare error:", err);
        Views.showError(err.message || "加载对比数据失败", function () {
          Pages.Compare.render();
        });
      });
  },

  _loadComparison: function () {
    var self = this;
    var ids = self._selectedIds.join(",");

    API.get("/analysis/compare?ids=" + ids)
      .then(function (data) {
        var companies = data.companies;
        var container = document.getElementById("compare-results");
        if (!container) return;

        var html = '<div class="card" style="margin-bottom:20px;">';
        html += '<div class="card-title">多维度对比雷达图</div>';
        html += '<div id="chart-compare-radar" class="chart-container" style="height:450px;"></div></div>';

        html += '<div class="section-grid" style="margin-bottom:20px;">';
        html += '<div class="card"><div class="card-title">平均评分对比</div>';
        html += '<div id="chart-bar-avg" class="chart-container" style="height:300px;"></div></div>';
        html += '<div class="card"><div class="card-title">作品数量对比</div>';
        html += '<div id="chart-bar-count" class="chart-container" style="height:300px;"></div></div>';
        html += '</div>';

        html += '<div class="card" style="margin-bottom:20px;">';
        html += '<div class="card-title">年度趋势对比</div>';
        html += '<div id="chart-yearly-compare" class="chart-container" style="height:380px;"></div></div>';

        html += '<div class="card"><div class="card-title">指标对比表</div>';
        html += '<div id="compare-table"></div></div>';
        html += '<div id="diff-panel-container"></div>';

        container.innerHTML = html;

        setTimeout(function () {
          Charts.renderMultiRadar("chart-compare-radar", companies);
          Charts.renderGroupedBar("chart-bar-avg", companies, "avg_score");
          Charts.renderGroupedBar("chart-bar-count", companies, "works_count");
          self._renderYearlyCompare("chart-yearly-compare", companies);
          self._renderCompareTable(companies);
          if (self._selectedIds.length === 2) self._loadDiff();
        }, 150);
      })
      .catch(function (err) {
        console.error("Compare load error:", err);
        var container = document.getElementById("compare-results");
        if (container) container.innerHTML = '<div class="error-state"><p>' + escapeHtml(err.message) + '</p></div>';
      });
  },

  _renderYearlyCompare: function (domId, companies) {
    var colors = CONFIG.getColors();
    var inst = Charts._getInstance(domId);
    if (!inst) return;

    var allYears = {};
    companies.forEach(function (c) {
      c.yearly_avg.forEach(function (y) { allYears[y.year] = true; });
    });
    var years = Object.keys(allYears).map(Number).sort(function (a, b) { return a - b; });

    var series = companies.map(function (c, i) {
      var yearMap = {};
      c.yearly_avg.forEach(function (y) { yearMap[y.year] = y.avg_score; });
      return {
        name: c.name, type: "line",
        data: years.map(function (y) { return yearMap[y] != null ? yearMap[y] : null; }),
        itemStyle: { color: colors.palette[i] }, smooth: true, connectNulls: true,
      };
    });

    inst.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: companies.map(function (c) { return c.name; }), textStyle: { color: colors.textSecondary } },
      xAxis: { type: "category", data: years.map(String) },
      yAxis: { type: "value", name: "平均评分" },
      series: series,
    }, true);
  },

  _renderCompareTable: function (companies) {
    var cols = [{ key: "name", label: "指标" }];
    companies.forEach(function (c) { cols.push({ key: "c" + c.id, label: c.name }); });

    var rowWorks = { name: "作品数量" };
    companies.forEach(function (c) { rowWorks["c" + c.id] = c.works_count; });
    var rowScore = { name: "平均评分" };
    companies.forEach(function (c) { rowScore["c" + c.id] = Analytics.formatScore(c.avg_score); });
    var rowRec = { name: "推荐率" };
    companies.forEach(function (c) { rowRec["c" + c.id] = c.recommended_ratio + "%"; });
    var rowTrash = { name: "翻车率" };
    companies.forEach(function (c) { rowTrash["c" + c.id] = c.trash_ratio + "%"; });

    var ctn = document.getElementById("compare-table");
    if (ctn) ctn.innerHTML = Views.dataTable(cols, [rowWorks, rowScore, rowRec, rowTrash]);
  },

  _loadDiff: function () {
    var a = this._selectedIds[0];
    var b = this._selectedIds[1];

    API.get("/analysis/compare/diff?a=" + a + "&b=" + b)
      .then(function (data) {
        var ctn = document.getElementById("diff-panel-container");
        if (!ctn) return;

        var absD = Math.abs(data.cohens_d);
        var interp = absD < 0.2 ? "差异极小" : absD < 0.5 ? "差异较小" : absD < 0.8 ? "中等差异" : "差异显著";

        var html = '<div class="diff-panel"><h3 style="margin-bottom:12px;">深度差异分析</h3>';
        html += '<p><strong>Cohen\'s d:</strong> ' + data.cohens_d + '（' + interp + '）</p>';
        html += '<p><strong>' + escapeHtml(data.company_a_name) + '</strong> vs <strong>' + escapeHtml(data.company_b_name) + '</strong></p>';
        html += '<p>波动率：' + escapeHtml(data.company_a_name) + ' σ=' + data.volatility_a + ' | ' + escapeHtml(data.company_b_name) + ' σ=' + data.volatility_b + '</p>';
        html += '<h4 style="margin-top:16px;">维度对决</h4>';

        data.dimensions.forEach(function (d) {
          var winText = d.winner === "a" ? '<span style="color:var(--color-success);font-weight:700;">' + data.company_a_name + ' 领先</span>' :
                        d.winner === "b" ? '<span style="color:var(--color-accent);font-weight:700;">' + data.company_b_name + ' 领先</span>' : "持平";
          html += '<div style="margin-bottom:8px;"><strong>' + escapeHtml(d.dimension) + ':</strong> ';
          html += d.company_a_value + ' vs ' + d.company_b_value + '（差值: ' + d.diff + '）— ' + winText + '</div>';
        });

        html += '</div>';
        ctn.innerHTML = html;
      })
      .catch(function (err) {
        console.error("Diff error:", err);
      });
  },
};
