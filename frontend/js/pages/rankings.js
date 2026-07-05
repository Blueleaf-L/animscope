/**
 * Rankings — #rankings
 */
Pages.Rankings = {
  _tab: "recommended",

  render: function (opts) {
    var self = this;
    Views.showSkeleton();
    self._tab = ((opts && opts.query) ? opts.query.tab : null) || "recommended";

    API.get("/analysis/rankings?tab=" + self._tab)
      .then(function (data) {
        var html = '<h1 style="margin-bottom:20px;">作品排行</h1>';
        html += '<div class="tabs">';
        html += '<button class="tab-btn' + (self._tab === "recommended" ? " active" : "") + '" data-tab="recommended">推荐排行</button>';
        html += '<button class="tab-btn' + (self._tab === "good" ? " active" : "") + '" data-tab="good">综合评分</button>';
        html += '<button class="tab-btn' + (self._tab === "trash" ? " active" : "") + '" data-tab="trash">翻车排行</button>';
        html += '</div>';
        html += '<div class="ranking-cards" id="ranking-cards"></div>';

        Views.setContent(html);

        var cardsHtml = "";
        var items = data.items.slice(0, 50);
        for (var i = 0; i < items.length; i++) {
          var item = items[i];
          var zHtml = item.z_score != null
            ? '<span style="color:' + (item.z_score > 0 ? 'var(--color-success)' : 'var(--color-danger)') + '">Z: ' + item.z_score + '</span>'
            : "";
          cardsHtml += '<div class="ranking-card" data-company-id="' + item.company_id + '">';
          cardsHtml += '<div class="rank">#' + item.rank + '</div>';
          cardsHtml += '<div class="company-name"><a href="#company/' + item.company_id + '">' + escapeHtml(item.company_name) + '</a> ' + Views.typeTag(item.company_type) + '</div>';
          cardsHtml += '<div style="display:flex;gap:16px;margin-top:8px;font-size:0.85rem;color:var(--text-secondary);">';
          cardsHtml += '<span>' + item.works_count + ' 部作品</span>';
          cardsHtml += '<span>均分 ' + Analytics.formatScore(item.avg_score) + '</span>';
          cardsHtml += zHtml + '</div>';
          cardsHtml += '<div style="display:flex;gap:12px;margin-top:6px;font-size:0.8rem;">';
          cardsHtml += '<span style="color:var(--rating-best);">' + item.recommended_count + ' 部推荐</span>';
          cardsHtml += '<span style="color:var(--rating-trash);">' + item.trash_count + ' 部翻车</span>';
          cardsHtml += '</div></div>';
        }
        document.getElementById("ranking-cards").innerHTML = cardsHtml;

        var tabs = document.querySelectorAll(".tab-btn");
        for (var j = 0; j < tabs.length; j++) {
          tabs[j].onclick = function () {
            Router.navigate(Analytics.buildHash("rankings", { tab: this.dataset.tab }));
          };
        }

        var cards = document.querySelectorAll(".ranking-card");
        for (var k = 0; k < cards.length; k++) {
          cards[k].onclick = function () {
            var cid = this.dataset.companyId;
            var hl = self._tab === "trash" ? "?highlight=trash" : "";
            window.location.hash = "#company/" + cid + hl;
          };
        }
      })
      .catch(function (err) {
        console.error("Rankings error:", err);
        Views.showError(err.message || "加载排行数据失败", function () {
          Pages.Rankings.render({ query: { tab: Pages.Rankings._tab } });
        });
      });
  },
};
