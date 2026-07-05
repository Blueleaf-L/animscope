/**
 * Companies Overview — #companies
 */
Pages.Companies = {
  _state: { page: 1, type: "", sort: "name", order: "asc", q: "" },

  render: function (opts) {
    var self = this;
    Views.showSkeleton();

    var query = (opts && opts.query) || {};
    self._state.page = parseInt(query.page) || 1;
    if (query.type !== undefined) self._state.type = query.type;
    if (query.q !== undefined) self._state.q = query.q;
    if (query.sort !== undefined) self._state.sort = query.sort;
    if (query.order !== undefined) self._state.order = query.order;

    var params = "?sort=" + self._state.sort + "&order=" + self._state.order +
      "&page=" + self._state.page + "&size=" + CONFIG.PAGE_SIZE;
    if (self._state.type) params += "&type=" + encodeURIComponent(self._state.type);
    if (self._state.q) params += "&q=" + encodeURIComponent(self._state.q);

    API.get("/companies" + params)
      .then(function (data) {
        var html = '<h1 style="margin-bottom:20px;">公司总览</h1>';

        html += '<div class="filter-bar">';
        html += '<div class="search-box">';
        html += '<input type="text" id="company-search" placeholder="搜索公司名称..." value="' + escapeHtml(self._state.q) + '">';
        html += '<button class="btn btn-primary btn-sm" id="search-btn">搜索</button>';
        html += '</div>';
        html += '<select id="type-filter">';
        html += '<option value="">全部类型</option>';
        html += '<option value="2D"' + (self._state.type === "2D" ? " selected" : "") + '>2D</option>';
        html += '<option value="3D"' + (self._state.type === "3D" ? " selected" : "") + '>3D</option>';
        html += '<option value="三渲二"' + (self._state.type === "三渲二" ? " selected" : "") + '>三渲二</option>';
        html += '</select>';
        html += '<select id="sort-select">';
        html += '<option value="name"' + (self._state.sort === "name" ? " selected" : "") + '>按名称排序</option>';
        html += '<option value="works_count"' + (self._state.sort === "works_count" ? " selected" : "") + '>按作品数排序</option>';
        html += '<option value="avg_score"' + (self._state.sort === "avg_score" ? " selected" : "") + '>按平均分排序</option>';
        html += '</select>';
        html += '<button class="btn btn-outline btn-sm" id="order-toggle">' + (self._state.order === "asc" ? "升序" : "降序") + '</button>';
        html += '</div>';

        if (!Charts.isMobile()) {
          html += '<div class="card" style="margin-bottom:20px;">';
          html += '<div class="card-title">公司分布气泡图 <span style="font-weight:400;font-size:0.85rem;color:var(--text-muted);">（点击气泡查看详情）</span>';
          html += '<button class="btn btn-sm btn-outline" id="bubble-toggle" style="margin-left:12px;">显示全部公司</button>';
          html += '</div>';
          html += '<div id="chart-bubble" class="chart-container" style="height:450px;"></div>';
          html += '</div>';
        }

        html += '<div id="company-table"></div>';
        html += '<div style="display:flex;justify-content:center;gap:8px;margin-top:20px;" id="pagination"></div>';

        Views.setContent(html);

        var columns = [
          { key: "name", label: "公司名称", render: function (v, row) { return Views.companyLink(row.id, v); } },
          { key: "type", label: "类型", render: function (v) { return Views.typeTag(v); } },
          { key: "works_count", label: "作品数" },
          { key: "avg_score", label: "平均评分", render: function (v) { return v != null ? Analytics.formatScore(v) : "-"; } },
        ];
        document.getElementById("company-table").innerHTML = Views.dataTable(columns, data.items, { emptyText: "暂无公司数据" });

        var pagHtml = "";
        for (var i = 1; i <= data.pages; i++) {
          pagHtml += '<button class="btn btn-sm ' + (i === data.page ? "btn-primary" : "btn-outline") + '" data-page="' + i + '">' + i + '</button>';
        }
        document.getElementById("pagination").innerHTML = pagHtml;

        if (!Charts.isMobile()) {
          var bubbleData = data.items.map(function (c) {
            return { name: c.name, type: c.type, works_count: c.works_count, avg_score: c.avg_score, id: c.id };
          });
          setTimeout(function () { Charts.renderBubbleChart("chart-bubble", bubbleData); }, 150);
        }

        self._attachEvents(data);

        // Bubble chart toggle: show all companies
        if (!Charts.isMobile()) {
          var showingAll = false;
          var btn = document.getElementById("bubble-toggle");
          var currentBubbleData = data.items.map(function (c) {
            return { name: c.name, type: c.type, works_count: c.works_count, avg_score: c.avg_score, id: c.id };
          });
          if (btn) {
            btn.onclick = function () {
              if (showingAll) {
                // Switch back to current page
                Charts.renderBubbleChart("chart-bubble", currentBubbleData);
                btn.textContent = "显示全部公司";
                showingAll = false;
              } else {
                // Fetch all companies for bubble chart
                API.get("/companies?size=100&sort=name").then(function (allData) {
                  var allBubble = allData.items.map(function (c) {
                    return { name: c.name, type: c.type, works_count: c.works_count, avg_score: c.avg_score, id: c.id };
                  });
                  Charts.renderBubbleChart("chart-bubble", allBubble);
                  btn.textContent = "显示当前页";
                  showingAll = true;
                }).catch(function () {
                  showToast("加载全部公司失败", "error");
                });
              }
            };
          }
        }
      })
      .catch(function (err) {
        console.error("Companies error:", err);
        Views.showError(err.message || "加载公司数据失败", function () {
          Pages.Companies.render({ query: Pages.Companies._state });
        });
      });
  },

  _attachEvents: function (data) {
    var self = this;

    function doSearch() {
      self._state.q = document.getElementById("company-search").value || "";
      self._state.page = 1;
      Router.navigate(Analytics.buildHash("companies", self._state));
    }

    var searchBtn = document.getElementById("search-btn");
    if (searchBtn) searchBtn.onclick = doSearch;

    var searchInput = document.getElementById("company-search");
    if (searchInput) searchInput.onkeydown = function (e) { if (e.key === "Enter") doSearch(); };

    var typeFilter = document.getElementById("type-filter");
    if (typeFilter) typeFilter.onchange = function () {
      self._state.type = this.value;
      self._state.page = 1;
      Router.navigate(Analytics.buildHash("companies", self._state));
    };

    var sortSelect = document.getElementById("sort-select");
    if (sortSelect) sortSelect.onchange = function () {
      self._state.sort = this.value;
      self._state.page = 1;
      Router.navigate(Analytics.buildHash("companies", self._state));
    };

    var orderToggle = document.getElementById("order-toggle");
    if (orderToggle) orderToggle.onclick = function () {
      self._state.order = self._state.order === "asc" ? "desc" : "asc";
      Router.navigate(Analytics.buildHash("companies", self._state));
    };

    var pagButtons = document.querySelectorAll("#pagination button[data-page]");
    for (var i = 0; i < pagButtons.length; i++) {
      pagButtons[i].onclick = function () {
        self._state.page = parseInt(this.dataset.page);
        Router.navigate(Analytics.buildHash("companies", self._state));
      };
    }
  },
};
