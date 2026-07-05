/**
 * ECharts rendering module.
 * All colors read from CONFIG.getColors() — never hardcoded.
 * Each render function handles responsive degradation for mobile.
 */

const Charts = {
  _instances: {},

  /** Get or create an ECharts instance tied to a DOM element. */
  _getInstance(domId) {
    if (this._instances[domId]) {
      this._instances[domId].dispose();
    }
    const dom = document.getElementById(domId);
    if (!dom) return null;
    const inst = echarts.init(dom, null, { renderer: "canvas" });
    this._instances[domId] = inst;
    return inst;
  },

  /** Dispose all chart instances (called on page navigation). */
  disposeAll() {
    Object.values(this._instances).forEach(inst => inst.dispose());
    this._instances = {};
  },

  /** Responsive check */
  isMobile() { return window.innerWidth < 768; },
  isTablet() { return window.innerWidth >= 768 && window.innerWidth < 1024; },

  /** ──────────── Ring Chart (Rating Distribution) ──────────── */
  renderRingChart(domId, data) {
    const colors = CONFIG.getColors();
    const inst = this._getInstance(domId);
    if (!inst) return;

    if (this.isMobile()) {
      // Degrade to bar chart
      inst.setOption({
        tooltip: { trigger: "axis" },
        xAxis: { type: "category", data: data.map(d => d.label), axisLabel: { color: colors.textSecondary } },
        yAxis: { type: "value", axisLabel: { color: colors.textSecondary } },
        series: [{
          type: "bar", data: data.map(d => ({ value: d.count, itemStyle: { color: colors.rating[d.label] || "#999" } })),
          emphasis: { itemStyle: { opacity: 0.8 } },
        }],
      }, true);
      return;
    }

    inst.setOption({
      tooltip: { trigger: "item", formatter: "{b}: {c} 部 ({d}%)" },
      legend: { orient: "vertical", left: "left", textStyle: { color: colors.textSecondary } },
      series: [{
        type: "pie", radius: ["40%", "70%"], center: ["60%", "50%"],
        label: { color: colors.textSecondary },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.2)" } },
        data: data.map(d => ({ name: d.label, value: d.count, itemStyle: { color: colors.rating[d.label] || "#999" } })),
      }],
    }, true);
  },

  /** ──────────── Rose / Nightingale Chart ──────────── */
  renderRoseChart(domId, data) {
    const colors = CONFIG.getColors();
    const inst = this._getInstance(domId);
    if (!inst) return;

    if (this.isMobile()) {
      // Degrade to horizontal bar chart
      inst.setOption({
        tooltip: { trigger: "axis" },
        yAxis: { type: "category", data: data.map(d => d.type), axisLabel: { color: colors.textSecondary } },
        xAxis: { type: "value", axisLabel: { color: colors.textSecondary } },
        series: [{
          type: "bar", data: data.map((d, i) => ({ value: d.count, itemStyle: { color: colors.palette[i] } })),
        }],
      }, true);
      return;
    }

    inst.setOption({
      tooltip: { trigger: "item" },
      legend: { top: "bottom", textStyle: { color: colors.textSecondary } },
      series: [{
        type: "pie", radius: [20, "80%"], center: ["50%", "50%"], roseType: "area",
        data: data.map((d, i) => ({ name: d.type, value: d.count, itemStyle: { color: colors.palette[i] } })),
      }],
    }, true);
  },

  /** ──────────── Dual-Axis Trend Line ──────────── */
  renderDualAxisTrend(domId, data) {
    const colors = CONFIG.getColors();
    const inst = this._getInstance(domId);
    if (!inst) return;

    const years = data.map(d => d.year);
    const counts = data.map(d => d.count);
    const avgs = data.map(d => d.avg_score);

    inst.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: ["作品数量", "平均评分"], textStyle: { color: colors.textSecondary } },
      xAxis: { type: "category", data: years, axisLabel: { color: colors.textSecondary } },
      yAxis: [
        { type: "value", name: "数量", axisLabel: { color: colors.textSecondary } },
        { type: "value", name: "平均分", axisLabel: { color: colors.textSecondary } },
      ],
      series: [
        { name: "作品数量", type: "bar", data: counts, itemStyle: { color: colors.palette[0], opacity: 0.7 }, yAxisIndex: 0 },
        { name: "平均评分", type: "line", data: avgs, itemStyle: { color: colors.palette[1] }, yAxisIndex: 1, smooth: true },
      ],
    }, true);
  },

  /** ──────────── Bubble / Scatter Chart ──────────── */
  renderBubbleChart(domId, data) {
    const colors = CONFIG.getColors();
    const inst = this._getInstance(domId);
    if (!inst) return;

    const typeColors = { "2D": colors.palette[0], "3D": colors.palette[1], "三渲二": colors.palette[2], "混合型": colors.palette[3] };

    const seriesByType = {};
    data.forEach(d => {
      const t = d.type || "3D";
      if (!seriesByType[t]) seriesByType[t] = [];
      seriesByType[t].push([d.works_count, d.avg_score || 0, d.name, d.id]);
    });

    inst.setOption({
      tooltip: {
        trigger: "item",
        formatter: p => `${p.data[2]}<br/>作品数: ${p.data[0]}<br/>平均分: ${(p.data[1]).toFixed(2)}`,
      },
      legend: { data: Object.keys(seriesByType), textStyle: { color: colors.textSecondary } },
      xAxis: { name: "作品数量", axisLabel: { color: colors.textSecondary } },
      yAxis: { name: "平均评分", axisLabel: { color: colors.textSecondary } },
      series: Object.entries(seriesByType).map(([t, pts]) => ({
        name: t, type: "scatter", symbolSize: d => Math.max(10, Math.min(d[0] * 3, 60)),
        data: pts,
        itemStyle: { color: typeColors[t] || colors.palette[0], opacity: 0.7 },
        emphasis: { itemStyle: { opacity: 1 } },
      })),
    }, true);

    // Click handler
    inst.off("click");
    inst.on("click", params => {
      if (params.data && params.data[3]) {
        window.location.hash = `#company/${params.data[3]}`;
      }
    });
  },

  /** ──────────── Multi-Line Trend by Type ──────────── */
  renderTypeTrendLines(domId, data) {
    const colors = CONFIG.getColors();
    const inst = this._getInstance(domId);
    if (!inst) return;

    const years = data.map(d => d.year);
    inst.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: ["2D平均分", "3D平均分", "三渲二平均分", "总数"], textStyle: { color: colors.textSecondary } },
      xAxis: { type: "category", data: years, axisLabel: { color: colors.textSecondary } },
      yAxis: [
        { type: "value", name: "平均评分", axisLabel: { color: colors.textSecondary } },
        { type: "value", name: "作品数", axisLabel: { color: colors.textSecondary } },
      ],
      series: [
        { name: "2D平均分", type: "line", data: data.map(d => d.type_2d_avg), itemStyle: { color: colors.palette[0] }, smooth: true },
        { name: "3D平均分", type: "line", data: data.map(d => d.type_3d_avg), itemStyle: { color: colors.palette[1] }, smooth: true },
        { name: "三渲二平均分", type: "line", data: data.map(d => d.type_hybrid_avg), itemStyle: { color: colors.palette[2] }, smooth: true },
        { name: "总数", type: "bar", data: data.map(d => d.total_count), itemStyle: { color: colors.palette[4], opacity: 0.4 }, yAxisIndex: 1 },
      ],
    }, true);
  },

  /** ──────────── Heatmap (ECharts) ──────────── */
  renderHeatmap(domId, heatmapData, companies, years) {
    const colors = CONFIG.getColors();
    const inst = this._getInstance(domId);
    if (!inst) return;

    const data = heatmapData.map(d => [years.indexOf(d.year), companies.indexOf(d.company_name), d.avg_score]);
    const maxVal = Math.max(...heatmapData.map(d => d.avg_score), 1);
    const minVal = Math.min(...heatmapData.map(d => d.avg_score), -1);

    inst.setOption({
      tooltip: {
        formatter: function (p) {
          var compName = companies[p.data[1]] || "";
          var yearVal = years[p.data[0]] || "";
          var score = (p.data[2] != null) ? p.data[2].toFixed(2) : "-";
          return compName + " " + yearVal + "年<br/>平均分: " + score;
        },
      },
      xAxis: { type: "category", data: years, axisLabel: this.isMobile() ? { rotate: 45 } : {}, splitArea: { show: true } },
      yAxis: { type: "category", data: companies, axisLabel: { color: colors.textSecondary } },
      visualMap: { min: minVal, max: maxVal, calculable: true, orient: "horizontal", left: "center", bottom: 0,
        inRange: { color: ["#e8405d", "#f5a623", "#3cc9a6", "#5b8def"] } },
      series: [{ type: "heatmap", data: data, label: { show: false }, emphasis: { itemStyle: { shadowBlur: 10 } } }],
    }, true);

    // Click handler for drill-down
    inst.off("click");
    inst.on("click", params => {
      if (params.data) {
        const year = years[params.data[0]];
        const compName = params.data[1];
        const evt = new CustomEvent("heatmap-click", { detail: { companyName: compName, year: year } });
        document.dispatchEvent(evt);
      }
    });
  },

  /** ──────────── Multi-Radar Comparison ──────────── */
  renderMultiRadar(domId, companies) {
    const colors = CONFIG.getColors();
    const inst = this._getInstance(domId);
    if (!inst) return;

    const indicators = [
      { name: "平均评分\nAvg Score", max: 1 },
      { name: "作品数量\nWorks", max: 1 },
      { name: "推荐率\nRecommended", max: 1 },
      { name: "良品率\nGood Rate", max: 1 },
      { name: "翻车率(反)\nTrash(inv)", max: 1 },
      { name: "最高分\nMax Score", max: 1 },
    ];

    const seriesData = companies.map(comp => {
      const maxWorks = Math.max(...companies.map(c => c.works_count), 1);
      const maxScore = Math.max(...companies.map(c => c.avg_score), 1);
      const minScore = Math.min(...companies.map(c => c.avg_score), -2);
      const range = maxScore - minScore || 1;
      return {
        name: comp.name,
        value: [
          (comp.avg_score - minScore) / range,
          comp.works_count / maxWorks,
          comp.recommended_ratio / 100,
          (100 - comp.trash_ratio) / 100,
          (maxScore > 0 ? (comp.avg_score > 0 ? comp.avg_score / maxScore : 0) : 0.3),
          (maxScore > 0 ? (comp.avg_score > 0 ? comp.avg_score / maxScore : 0) : 0.3),
        ],
      };
    });

    inst.setOption({
      tooltip: {},
      legend: { data: companies.map(c => c.name), textStyle: { color: colors.textSecondary } },
      radar: {
        indicator: indicators,
        axisName: { color: colors.textSecondary },
        splitArea: { areaStyle: { color: [colors.bgCard] } },
      },
      series: [{
        type: "radar",
        data: seriesData.map((d, i) => ({
          ...d,
          itemStyle: { color: colors.palette[i] },
          areaStyle: { color: colors.palette[i], opacity: 0.1 },
        })),
      }],
    }, true);
  },

  /** ──────────── Grouped Bar Chart ──────────── */
  renderGroupedBar(domId, companies, metric) {
    const colors = CONFIG.getColors();
    const inst = this._getInstance(domId);
    if (!inst) return;

    inst.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: companies.map(c => c.name), textStyle: { color: colors.textSecondary } },
      xAxis: { type: "category", data: [metric], axisLabel: { color: colors.textSecondary } },
      yAxis: { type: "value", axisLabel: { color: colors.textSecondary } },
      series: companies.map((c, i) => ({
        name: c.name, type: "bar",
        itemStyle: { color: colors.palette[i] },
        data: [{ value: metric === "avg_score" ? c.avg_score : metric === "works_count" ? c.works_count : c.recommended_ratio }],
      })),
    }, true);
  },

  /** ──────────── Company Timeline (Scatter) ──────────── */
  renderTimeline(domId, works) {
    const colors = CONFIG.getColors();
    const inst = this._getInstance(domId);
    if (!inst) return;

    const data = works
      .filter(w => w.year)
      .map(w => ({
        value: [w.year, w.rating_score || 0],
        name: w.name,
        label: w.rating_label,
        itemStyle: { color: colors.rating[w.rating_label] || "#999" },
      }));

    // Calculate actual year range from data
    var years = data.map(function (d) { return d.value[0]; });
    var minYear = Math.min.apply(null, years) - 1;
    var maxYear = Math.max.apply(null, years) + 1;

    inst.setOption({
      tooltip: { trigger: "item", formatter: function (p) { return p.name + "<br/>年份: " + p.value[0] + "<br/>评分: " + p.value[1]; } },
      xAxis: { type: "value", name: "年份", min: minYear, max: maxYear, axisLabel: { color: colors.textSecondary } },
      yAxis: { type: "value", name: "评分", axisLabel: { color: colors.textSecondary } },
      series: [{
        type: "scatter", symbolSize: 15,
        data: data,
        markLine: { data: [{ yAxis: 0, lineStyle: { color: colors.textSecondary, type: "dashed" } }] },
      }],
    }, true);
  },

  /** ──────────── Refresh all charts after theme change ──────────── */
  refreshAllThemes() {
    Object.values(this._instances).forEach(inst => {
      // Re-render is handled by each page on navigation; just dispose for now
      inst.dispose();
    });
    this._instances = {};
  },
};
