/**
 * Rankings — static version
 */
Pages.Rankings = {
  _tab: "recommended",
  render: function (opts) {
    var self = this;
    Views.showSkeleton();
    self._tab = ((opts && opts.query) ? opts.query.tab : null) || "recommended";
    StaticData.load("rankings_" + self._tab)
      .then(function (data) {
        var html = '<h1 style="margin-bottom:20px;">作品排行</h1>';
        html += '<div class="tabs"><button class="tab-btn' + (self._tab==="recommended"?" active":"") + '" data-tab="recommended">推荐排行</button><button class="tab-btn' + (self._tab==="good"?" active":"") + '" data-tab="good">综合评分</button><button class="tab-btn' + (self._tab==="trash"?" active":"") + '" data-tab="trash">翻车排行</button></div>';
        html += '<div class="ranking-cards" id="ranking-cards"></div>';
        Views.setContent(html);

        var cards = "";
        data.items.slice(0, 50).forEach(function (item) {
          cards += '<div class="ranking-card" data-company-id="' + item.company_id + '"><div class="rank">#' + item.rank + '</div><div class="company-name"><a href="#company/' + item.company_id + '">' + escapeHtml(item.company_name) + '</a> ' + Views.typeTag(item.company_type) + '</div><div style="display:flex;gap:16px;margin-top:8px;font-size:0.85rem;color:var(--text-secondary);"><span>' + item.works_count + ' 部</span><span>均分 ' + Analytics.formatScore(item.avg_score) + '</span>' + (item.z_score!=null?'<span style="color:'+(item.z_score>0?'var(--color-success)':'var(--color-danger)')+'">Z:'+item.z_score+'</span>':'') + '</div><div style="display:flex;gap:12px;margin-top:6px;font-size:0.8rem;"><span style="color:var(--rating-best);">' + item.recommended_count + '推荐</span><span style="color:var(--rating-trash);">' + item.trash_count + '翻车</span></div></div>';
        });
        document.getElementById("ranking-cards").innerHTML = cards;

        document.querySelectorAll(".tab-btn").forEach(function (b) { b.onclick = function () { self._tab = this.dataset.tab; Pages.Rankings.render({ query: { tab: self._tab } }); }; });
        document.querySelectorAll(".ranking-card").forEach(function (c) { c.onclick = function () { window.location.hash = "#company/" + this.dataset.companyId + (self._tab==="trash"?"?highlight=trash":""); }; });
      })
      .catch(function (err) { Views.showError("加载排行失败", function () { Pages.Rankings.render(); }); });
  },
};
