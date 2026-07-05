/**
 * Works Search — #search
 */
Pages.Search = {
  _state: { q: "", year: "", rating: "", type: "", page: 1, sort: "year", order: "desc" },

  render: function (opts) {
    var self = this;
    Views.showSkeleton();

    var query = (opts && opts.query) || {};
    if (query.q !== undefined) self._state.q = query.q;
    if (query.year !== undefined) self._state.year = query.year;
    if (query.rating !== undefined) self._state.rating = query.rating;
    if (query.type !== undefined) self._state.type = query.type;
    self._state.page = parseInt(query.page) || 1;

    var params = "?sort=" + self._state.sort + "&order=" + self._state.order +
      "&page=" + self._state.page + "&size=" + CONFIG.PAGE_SIZE;
    if (self._state.q) params += "&q=" + encodeURIComponent(self._state.q);
    if (self._state.year) params += "&year=" + self._state.year;
    if (self._state.rating) params += "&rating=" + encodeURIComponent(self._state.rating);
    if (self._state.type) params += "&type=" + encodeURIComponent(self._state.type);

    API.get("/works" + params)
      .then(function (data) {
        var html = '<h1 style="margin-bottom:20px;">作品搜索</h1>';
        html += '<div class="filter-bar">';
        html += '<div class="search-box">';
        html += '<input type="text" id="work-search-input" placeholder="搜索作品名称..." value="' + escapeHtml(self._state.q) + '">';
        html += '<button class="btn btn-primary btn-sm" id="search-execute">搜索</button></div>';
        html += '<input type="number" id="year-input" placeholder="年份" value="' + escapeHtml(self._state.year) + '" style="width:80px;">';
        html += '<select id="rating-filter"><option value="">全部评级</option>';
        CONFIG.RATING_ORDER.forEach(function (r) {
          html += '<option value="' + r + '"' + (self._state.rating === r ? " selected" : "") + '>' + r + '</option>';
        });
        html += '</select>';
        html += '<select id="type-filter"><option value="">全部类型</option>';
        html += '<option value="2D"' + (self._state.type === "2D" ? " selected" : "") + '>2D</option>';
        html += '<option value="3D"' + (self._state.type === "3D" ? " selected" : "") + '>3D</option>';
        html += '<option value="三渲二"' + (self._state.type === "三渲二" ? " selected" : "") + '>三渲二</option>';
        html += '</select></div>';
        html += '<div id="search-results-table"></div>';
        html += '<div style="text-align:center;color:var(--text-muted);margin-top:12px;">共 ' + data.total + ' 条结果，第 ' + data.page + '/' + data.pages + ' 页</div>';
        html += '<div style="display:flex;justify-content:center;gap:8px;margin-top:16px;" id="pagination"></div>';

        Views.setContent(html);

        var columns = [
          { key: "name", label: "作品名称" },
          { key: "company_name", label: "所属公司", render: function (v, row) { return Views.companyLink(row.company_id, v); } },
          { key: "year", label: "年份", render: function (v) { return v || "-"; } },
          { key: "rating_label", label: "评级", render: function (v) { return Views.ratingBadge(v); } },
          { key: "rating_score", label: "评分", render: function (v) { return v != null ? Analytics.formatScore(v) : "-"; } },
        ];
        document.getElementById("search-results-table").innerHTML = Views.dataTable(columns, data.items, { emptyText: "未找到匹配作品" });

        var pagHtml = "";
        for (var i = 1; i <= Math.min(data.pages, 10); i++) {
          pagHtml += '<button class="btn btn-sm ' + (i === data.page ? "btn-primary" : "btn-outline") + '" data-page="' + i + '">' + i + '</button>';
        }
        document.getElementById("pagination").innerHTML = pagHtml;

        self._attachEvents();
      })
      .catch(function (err) {
        console.error("Search error:", err);
        Views.showError(err.message || "搜索失败", function () {
          Pages.Search.render({ query: Pages.Search._state });
        });
      });
  },

  _attachEvents: function () {
    var self = this;
    function doSearch() {
      self._state.q = document.getElementById("work-search-input").value || "";
      self._state.year = document.getElementById("year-input").value || "";
      self._state.rating = document.getElementById("rating-filter").value || "";
      self._state.type = document.getElementById("type-filter").value || "";
      self._state.page = 1;
      Router.navigate(Analytics.buildHash("search", self._state));
    }
    var b = document.getElementById("search-execute"); if (b) b.onclick = doSearch;
    var inp = document.getElementById("work-search-input"); if (inp) inp.onkeydown = function (e) { if (e.key === "Enter") doSearch(); };
    var yf = document.getElementById("year-input"); if (yf) yf.onchange = doSearch;
    var rf = document.getElementById("rating-filter"); if (rf) rf.onchange = doSearch;
    var tf = document.getElementById("type-filter"); if (tf) tf.onchange = doSearch;
    var pbs = document.querySelectorAll("#pagination button[data-page]");
    for (var i = 0; i < pbs.length; i++) {
      pbs[i].onclick = function () {
        self._state.page = parseInt(this.dataset.page);
        Router.navigate(Analytics.buildHash("search", self._state));
      };
    }
  },
};
