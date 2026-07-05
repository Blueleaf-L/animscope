/**
 * Companies Overview — static version
 */
Pages.Companies = {
  _state: { page: 1, type: "", sort: "name", order: "asc", q: "" },
  _allData: null,

  render: function (opts) {
    var self = this;
    Views.showSkeleton();
    var query = (opts && opts.query) || {};
    if (query.type !== undefined) self._state.type = query.type;
    if (query.q !== undefined) self._state.q = query.q;
    if (query.sort !== undefined) self._state.sort = query.sort;
    if (query.order !== undefined) self._state.order = query.order;
    self._state.page = parseInt(query.page) || 1;

    StaticData.load("companies_lite")
      .then(function (data) {
        self._allData = data;
        self._renderList(data);
      })
      .catch(function (err) {
        Views.showError("加载公司数据失败", function () { Pages.Companies.render(); });
      });
  },

  _renderList: function (data) {
    var self = this;
    var filtered = data;

    // Filter
    if (self._state.type) {
      filtered = filtered.filter(function (c) { return c.type === self._state.type; });
    }
    if (self._state.q) {
      var q = self._state.q.toLowerCase();
      filtered = filtered.filter(function (c) { return c.name.toLowerCase().indexOf(q) >= 0; });
    }

    // Sort
    var sk = self._state.sort, so = self._state.order;
    filtered.sort(function (a, b) {
      var va, vb;
      if (sk === "works_count") { va = a.works_count; vb = b.works_count; }
      else if (sk === "avg_score") { va = a.avg_score || 0; vb = b.avg_score || 0; }
      else { va = a.name; vb = b.name; }
      return so === "asc" ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
    });

    // Paginate
    var total = filtered.length;
    var pages = Math.ceil(total / CONFIG.PAGE_SIZE) || 1;
    if (self._state.page > pages) self._state.page = pages;
    var start = (self._state.page - 1) * CONFIG.PAGE_SIZE;
    var items = filtered.slice(start, start + CONFIG.PAGE_SIZE);

    var html = '<h1 style="margin-bottom:20px;">公司总览</h1>';
    html += '<div class="filter-bar">';
    html += '<div class="search-box"><input type="text" id="company-search" placeholder="搜索公司..." value="' + escapeHtml(self._state.q) + '"><button class="btn btn-primary btn-sm" id="search-btn">搜索</button></div>';
    html += '<select id="type-filter"><option value="">全部类型</option><option value="2D"' + (self._state.type==="2D"?" selected":"") + '>2D</option><option value="3D"' + (self._state.type==="3D"?" selected":"") + '>3D</option><option value="三渲二"' + (self._state.type==="三渲二"?" selected":"") + '>三渲二</option></select>';
    html += '<select id="sort-select"><option value="name"' + (sk==="name"?" selected":"") + '>按名称</option><option value="works_count"' + (sk==="works_count"?" selected":"") + '>按作品数</option><option value="avg_score"' + (sk==="avg_score"?" selected":"") + '>按平均分</option></select>';
    html += '<button class="btn btn-outline btn-sm" id="order-toggle">' + (so==="asc"?"升序":"降序") + '</button></div>';

    if (!Charts.isMobile()) {
      html += '<div class="card" style="margin-bottom:20px;"><div class="card-title">公司分布气泡图 <button class="btn btn-sm btn-outline" id="bubble-toggle" style="margin-left:12px;">显示全部公司</button></div><div id="chart-bubble" class="chart-container" style="height:450px;"></div></div>';
    }

    html += '<div id="company-table"></div>';
    html += '<div style="display:flex;justify-content:center;gap:8px;margin-top:20px;" id="pagination"></div>';

    Views.setContent(html);

    // Table
    var cols = [
      { key: "name", label: "公司名称", render: function (v, row) { return Views.companyLink(row.id, v); } },
      { key: "type", label: "类型", render: function (v) { return Views.typeTag(v); } },
      { key: "works_count", label: "作品数" },
      { key: "avg_score", label: "平均评分", render: function (v) { return v != null ? Analytics.formatScore(v) : "-"; } },
    ];
    document.getElementById("company-table").innerHTML = Views.dataTable(cols, items, { emptyText: "暂无数据" });

    // Pagination
    var ph = "";
    for (var i = 1; i <= pages; i++) ph += '<button class="btn btn-sm ' + (i===self._state.page?"btn-primary":"btn-outline") + '" data-page="' + i + '">' + i + '</button>';
    document.getElementById("pagination").innerHTML = ph;

    // Bubble chart
    if (!Charts.isMobile()) {
      var bd = items.map(function (c) { return { name: c.name, type: c.type, works_count: c.works_count, avg_score: c.avg_score, id: c.id }; });
      setTimeout(function () { Charts.renderBubbleChart("chart-bubble", bd); }, 150);

      // Toggle all companies
      var showingAll = false, currentBD = bd;
      document.getElementById("bubble-toggle").onclick = function () {
        if (showingAll) { Charts.renderBubbleChart("chart-bubble", currentBD); this.textContent = "显示全部公司"; showingAll = false; }
        else {
          var allBD = data.map(function (c) { return { name: c.name, type: c.type, works_count: c.works_count, avg_score: c.avg_score, id: c.id }; });
          Charts.renderBubbleChart("chart-bubble", allBD); this.textContent = "显示当前页"; showingAll = true;
        }
      };
    }

    self._attachEvents(pages);
  },

  _attachEvents: function (pages) {
    var self = this;
    function doSearch() {
      self._state.q = document.getElementById("company-search").value || "";
      self._state.page = 1;
      self._renderList(self._allData);
    }
    var sb = document.getElementById("search-btn"); if (sb) sb.onclick = doSearch;
    var si = document.getElementById("company-search"); if (si) si.onkeydown = function (e) { if (e.key === "Enter") doSearch(); };
    var tf = document.getElementById("type-filter"); if (tf) tf.onchange = function () { self._state.type = this.value; self._state.page = 1; self._renderList(self._allData); };
    var ss = document.getElementById("sort-select"); if (ss) ss.onchange = function () { self._state.sort = this.value; self._state.page = 1; self._renderList(self._allData); };
    var ot = document.getElementById("order-toggle"); if (ot) ot.onclick = function () { self._state.order = self._state.order === "asc" ? "desc" : "asc"; self._renderList(self._allData); };
    var pbs = document.querySelectorAll("#pagination button[data-page]");
    for (var i = 0; i < pbs.length; i++) { pbs[i].onclick = function () { self._state.page = parseInt(this.dataset.page); self._renderList(self._allData); }; }
  },
};
