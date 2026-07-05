/**
 * Works Search — static version
 */
Pages.Search = {
  _state: { q: "", year: "", rating: "", type: "", page: 1, sort: "year", order: "desc" },
  render: function (opts) {
    var self = this; Views.showSkeleton();
    var q = (opts && opts.query) || {};
    if (q.q !== undefined) self._state.q = q.q; if (q.year !== undefined) self._state.year = q.year; if (q.rating !== undefined) self._state.rating = q.rating; if (q.type !== undefined) self._state.type = q.type; self._state.page = parseInt(q.page) || 1;

    var yearNum = self._state.year ? parseInt(self._state.year) : null;
    StaticData.searchWorks(self._state.q, yearNum, self._state.rating, self._state.type, self._state.sort, self._state.order, self._state.page, CONFIG.PAGE_SIZE)
      .then(function (data) {
        var html = '<h1 style="margin-bottom:20px;">作品搜索</h1><div class="filter-bar"><div class="search-box"><input type="text" id="work-search-input" placeholder="搜索作品..." value="' + escapeHtml(self._state.q) + '"><button class="btn btn-primary btn-sm" id="search-execute">搜索</button></div><input type="number" id="year-input" placeholder="年份" value="' + escapeHtml(self._state.year) + '" style="width:80px;"><select id="rating-filter"><option value="">全部评级</option>';
        CONFIG.RATING_ORDER.forEach(function (r) { html += '<option value="' + r + '"' + (self._state.rating===r?" selected":"") + '>' + r + '</option>'; });
        html += '</select><select id="type-filter"><option value="">全部类型</option><option value="2D"' + (self._state.type==="2D"?" selected":"") + '>2D</option><option value="3D"' + (self._state.type==="3D"?" selected":"") + '>3D</option><option value="三渲二"' + (self._state.type==="三渲二"?" selected":"") + '>三渲二</option></select></div>';
        html += '<div id="search-results-table"></div><div style="text-align:center;color:var(--text-muted);margin-top:12px;">共 ' + data.total + ' 条，第 ' + data.page + '/' + data.pages + ' 页</div><div style="display:flex;justify-content:center;gap:8px;margin-top:16px;" id="pagination"></div>';
        Views.setContent(html);

        var cols = [{ key:"name",label:"作品" },{ key:"company_name",label:"公司",render:function(v,row){return Views.companyLink(row.company_id,v);} },{ key:"year",label:"年份",render:function(v){return v||"-";} },{ key:"rating_label",label:"评级",render:function(v){return Views.ratingBadge(v);} },{ key:"rating_score",label:"评分",render:function(v){return v!=null?Analytics.formatScore(v):"-";} }];
        document.getElementById("search-results-table").innerHTML = Views.dataTable(cols, data.items, { emptyText: "无结果" });
        var ph = ""; for (var i = 1; i <= Math.min(data.pages, 10); i++) ph += '<button class="btn btn-sm ' + (i===data.page?"btn-primary":"btn-outline") + '" data-page="' + i + '">' + i + '</button>';
        document.getElementById("pagination").innerHTML = ph;
        self._attachEvents();
      }).catch(function (err) { Views.showError("搜索失败", function () { Pages.Search.render(); }); });
  },
  _attachEvents: function () {
    var self = this;
    function doSearch() { self._state.q = document.getElementById("work-search-input").value || ""; self._state.year = document.getElementById("year-input").value || ""; self._state.rating = document.getElementById("rating-filter").value || ""; self._state.type = document.getElementById("type-filter").value || ""; self._state.page = 1; Pages.Search.render({ query: self._state }); }
    var b = document.getElementById("search-execute"); if (b) b.onclick = doSearch;
    var inp = document.getElementById("work-search-input"); if (inp) inp.onkeydown = function (e) { if (e.key === "Enter") doSearch(); };
    var yf = document.getElementById("year-input"); if (yf) yf.onchange = doSearch;
    var rf = document.getElementById("rating-filter"); if (rf) rf.onchange = doSearch;
    var tf = document.getElementById("type-filter"); if (tf) tf.onchange = doSearch;
    document.querySelectorAll("#pagination button[data-page]").forEach(function (pb) { pb.onclick = function () { self._state.page = parseInt(this.dataset.page); Pages.Search.render({ query: self._state }); }; });
  },
};
