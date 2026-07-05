/**
 * Comparison — static version
 */
Pages.Compare = {
  _selectedIds: [],
  render: function (opts) {
    var self = this; Views.showSkeleton();
    if (opts && opts.query && opts.query.ids) self._selectedIds = opts.query.ids.split(",").map(Number).filter(Boolean);
    StaticData.load("companies_lite").then(function (data) {
      var html = '<h1 style="margin-bottom:20px;">公司对比</h1><div class="card" style="margin-bottom:20px;"><div class="card-title">选择对比公司（2-4家）</div><p style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:12px;">点击选择/取消</p><div class="compare-selector" id="compare-selector">';
      data.forEach(function (c) { var s = self._selectedIds.indexOf(c.id) >= 0; html += '<span class="compare-chip' + (s?" selected":"") + '" data-id="' + c.id + '">' + (s?'<span class="remove">X</span>':'') + escapeHtml(c.name) + '</span>'; });
      html += '</div><button class="btn btn-primary" id="compare-btn"' + (self._selectedIds.length < 2 ? " disabled" : "") + '>对比（' + self._selectedIds.length + '家）</button></div><div id="compare-results"></div>';
      Views.setContent(html);
      document.querySelectorAll(".compare-chip").forEach(function (ch) { ch.onclick = function () { var id = parseInt(this.dataset.id), idx = self._selectedIds.indexOf(id); if (idx >= 0) self._selectedIds.splice(idx, 1); else if (self._selectedIds.length < 4) self._selectedIds.push(id); else { showToast("最多4家","error"); return; } Pages.Compare.render({ query: { ids: self._selectedIds.join(",") } }); }; });
      document.getElementById("compare-btn").onclick = function () { if (self._selectedIds.length >= 2) Pages.Compare.render({ query: { ids: self._selectedIds.join(",") } }); };
      if (self._selectedIds.length >= 2) self._loadResults();
    }).catch(function (err) { Views.showError("加载失败", function () { Pages.Compare.render(); }); });
  },
  _loadResults: function () {
    var self = this;
    StaticData.compareCompanies(self._selectedIds).then(function (data) {
      var ctn = document.getElementById("compare-results"); if (!ctn) return;
      var co = data.companies;
      ctn.innerHTML = '<div class="card" style="margin-bottom:20px;"><div class="card-title">多维度雷达图</div><div id="chart-compare-radar" class="chart-container" style="height:450px;"></div></div><div class="section-grid" style="margin-bottom:20px;"><div class="card"><div class="card-title">平均评分对比</div><div id="chart-bar-avg" class="chart-container" style="height:300px;"></div></div><div class="card"><div class="card-title">作品数量对比</div><div id="chart-bar-count" class="chart-container" style="height:300px;"></div></div></div><div class="card" style="margin-bottom:20px;"><div class="card-title">年度趋势对比</div><div id="chart-yearly-compare" class="chart-container" style="height:380px;"></div></div><div class="card"><div class="card-title">指标对比表</div><div id="compare-table"></div></div><div id="diff-panel-container"></div>';
      setTimeout(function () {
        Charts.renderMultiRadar("chart-compare-radar", co);
        Charts.renderGroupedBar("chart-bar-avg", co, "avg_score");
        Charts.renderGroupedBar("chart-bar-count", co, "works_count");
        // Yearly overlay
        var inst = Charts._getInstance("chart-yearly-compare"); if (!inst) return;
        var allY = {}; co.forEach(function (c) { c.yearly_avg.forEach(function (y) { allY[y.year] = true; }); });
        var yrs = Object.keys(allY).map(Number).sort(function (a,b){return a-b;});
        inst.setOption({ tooltip:{trigger:"axis"}, legend:{data:co.map(function(c){return c.name;})}, xAxis:{type:"category",data:yrs.map(String)}, yAxis:{type:"value",name:"平均评分"}, series:co.map(function(c,i){var m={}; c.yearly_avg.forEach(function(y){m[y.year]=y.avg_score;}); return {name:c.name,type:"line",data:yrs.map(function(y){return m[y]!=null?m[y]:null;}),itemStyle:{color:CONFIG.getColors().palette[i]},smooth:true,connectNulls:true};}) }, true);
        // Table
        var rw = {name:"作品数量"}, rs = {name:"平均评分"}, rr = {name:"推荐率"}, rt = {name:"翻车率"};
        co.forEach(function(c){rw["c"+c.id]=c.works_count; rs["c"+c.id]=Analytics.formatScore(c.avg_score); rr["c"+c.id]=c.recommended_ratio+"%"; rt["c"+c.id]=c.trash_ratio+"%";});
        var cols = [{key:"name",label:"指标"}]; co.forEach(function(c){cols.push({key:"c"+c.id,label:c.name});});
        var tc = document.getElementById("compare-table"); if (tc) tc.innerHTML = Views.dataTable(cols, [rw,rs,rr,rt]);
        if (self._selectedIds.length === 2) self._loadDiff();
      }, 150);
    }).catch(function (err) { console.error(err); });
  },
  _loadDiff: function () {
    var a = this._selectedIds[0], b = this._selectedIds[1];
    StaticData.compareDiff(a, b).then(function (data) {
      var ctn = document.getElementById("diff-panel-container"); if (!ctn) return;
      var absD = Math.abs(data.cohens_d), interp = absD < 0.2 ? "极小" : absD < 0.5 ? "较小" : absD < 0.8 ? "中等" : "显著";
      var html = '<div class="diff-panel"><h3>深度差异分析</h3><p>Cohen\'s d: ' + data.cohens_d + '（' + interp + '）</p>';
      html += '<p>' + escapeHtml(data.company_a_name) + ' vs ' + escapeHtml(data.company_b_name) + '</p><p>波动率: ' + data.company_a_name + ' sigma=' + data.volatility_a + ' | ' + data.company_b_name + ' sigma=' + data.volatility_b + '</p><h4>维度对决</h4>';
      data.dimensions.forEach(function (d) { html += '<div style="margin-bottom:8px;"><strong>' + d.dimension + ':</strong> ' + d.company_a_value + ' vs ' + d.company_b_value + '（差值:' + d.diff + '）— ' + (d.winner==="a"?'<span style="color:var(--color-success)">'+data.company_a_name+' 领先</span>':d.winner==="b"?'<span style="color:var(--color-accent)">'+data.company_b_name+' 领先</span>':"持平") + '</div>'; });
      html += '</div>'; ctn.innerHTML = html;
    }).catch(function () {});
  },
};
