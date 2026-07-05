/**
 * Static data loader for GitHub Pages deployment.
 * Loads pre-computed JSON files instead of calling a backend API.
 */

var apiError = (function () {
  function apiError(message, code) {
    this.name = "ApiError";
    this.message = message;
    this.code = code;
  }
  apiError.prototype = Object.create(Error.prototype);
  return apiError;
})();

var StaticData = {
  _cache: {},
  _base: "data/static",

  /** Load a JSON file from data/static/ (with cache). */
  load: function (name) {
    var self = this;
    if (self._cache[name]) return Promise.resolve(self._cache[name]);

    return fetch(self._base + "/" + name + ".json")
      .then(function (res) {
        if (!res.ok) throw new apiError("File not found: " + name, "HTTP_" + res.status);
        return res.json();
      })
      .then(function (data) {
        self._cache[name] = data;
        return data;
      })
      .catch(function (err) {
        if (err instanceof apiError) throw err;
        throw new apiError("Failed to load data: " + name, "NETWORK");
      });
  },

  /** Preload common data files for faster navigation. */
  preload: function () {
    var self = this;
    self.load("overview");
    self.load("companies_full");
    self.load("companies_lite");
    self.load("rankings_recommended");
    self.load("trends");
  },

  /** Find a company by ID from the full company data. */
  findCompany: function (id) {
    var self = this;
    return self.load("companies_full").then(function (data) {
      for (var i = 0; i < data.length; i++) {
        if (data[i].id === id) return data[i];
      }
      throw new apiError("Company not found: " + id, "NOT_FOUND");
    });
  },

  /** Search works client-side by keyword, year, rating, type. */
  searchWorks: function (q, year, rating, type, sort, order, page, size) {
    var self = this;
    return self.load("companies_full").then(function (companies) {
      var allWorks = [];
      companies.forEach(function (c) {
        (c.works || []).forEach(function (w) {
          w.company_name = c.name;
          w.company_type = c.type;
        });
        allWorks = allWorks.concat(c.works || []);
      });

      // Filter
      var filtered = allWorks.filter(function (w) {
        if (q && w.name.indexOf(q) === -1) return false;
        if (year && w.year !== year) return false;
        if (rating && w.rating_label !== rating) return false;
        if (type && w.company_type !== type) return false;
        return true;
      });

      // Sort
      filtered.sort(function (a, b) {
        var va, vb;
        if (sort === "year") { va = a.year || 0; vb = b.year || 0; }
        else if (sort === "rating_score") { va = a.rating_score || 0; vb = b.rating_score || 0; }
        else { va = a.name || ""; vb = b.name || ""; }
        return order === "asc" ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
      });

      var total = filtered.length;
      var start = (page - 1) * size;
      var items = filtered.slice(start, start + size);
      var pages = Math.ceil(total / size) || 1;

      return { items: items, total: total, page: page, size: size, pages: pages };
    });
  },

  /** Compute comparison between 2-4 companies client-side. */
  compareCompanies: function (ids) {
    var self = this;
    return self.load("companies_full").then(function (companies) {
      var selected = companies.filter(function (c) { return ids.indexOf(c.id) >= 0; });

      var result = selected.map(function (c) {
        var works = c.works || [];
        var scores = [];
        var recCount = 0, trashCount = 0, yearData = {};
        works.forEach(function (w) {
          if (w.rating_score != null) scores.push(w.rating_score);
          if (w.rating_label === "年度推荐") recCount++;
          if (w.rating_label === "拉了" || w.rating_label === "史") trashCount++;
          if (w.year) {
            if (!yearData[w.year]) yearData[w.year] = [];
            yearData[w.year].push(w.rating_score);
          }
        });
        var avgScore = scores.length ? scores.reduce(function (s, v) { return s + v; }, 0) / scores.length : 0;
        var recRatio = works.length ? (recCount / works.length * 100) : 0;
        var trashRatio = works.length ? (trashCount / works.length * 100) : 0;
        var yearlyAvg = Object.keys(yearData).sort().map(function (y) {
          var ys = yearData[y];
          return { year: parseInt(y), avg_score: Math.round(ys.reduce(function (s, v) { return s + v; }, 0) / ys.length * 100) / 100 };
        });

        return {
          id: c.id, name: c.name, type: c.type, works_count: works.length,
          avg_score: Math.round(avgScore * 100) / 100,
          recommended_ratio: Math.round(recRatio * 10) / 10,
          trash_ratio: Math.round(trashRatio * 10) / 10,
          yearly_avg: yearlyAvg,
        };
      });

      return { companies: result };
    });
  },

  /** Compute Cohen's d diff between two companies client-side. */
  compareDiff: function (a, b) {
    var self = this;
    return self.load("companies_full").then(function (companies) {
      var ca = null, cb = null;
      companies.forEach(function (c) { if (c.id === a) ca = c; if (c.id === b) cb = c; });
      if (!ca || !cb) throw new apiError("Company not found", "NOT_FOUND");

      var sa = [], sb = [];
      (ca.works || []).forEach(function (w) { if (w.rating_score != null) sa.push(w.rating_score); });
      (cb.works || []).forEach(function (w) { if (w.rating_score != null) sb.push(w.rating_score); });

      if (!sa.length || !sb.length) throw new apiError("Insufficient data", "NO_DATA");

      var meanA = sa.reduce(function (s, v) { return s + v; }, 0) / sa.length;
      var meanB = sb.reduce(function (s, v) { return s + v; }, 0) / sb.length;
      var varA = sa.reduce(function (s, v) { return s + (v - meanA) * (v - meanA); }, 0) / (sa.length - 1);
      var varB = sb.reduce(function (s, v) { return s + (v - meanB) * (v - meanB); }, 0) / (sb.length - 1);
      var pooled = Math.sqrt(((sa.length - 1) * varA + (sb.length - 1) * varB) / (sa.length + sb.length - 2));
      var cohensD = pooled > 0 ? Math.round((meanA - meanB) / pooled * 1000) / 1000 : 0;

      var stdA = Math.sqrt(varA), stdB = Math.sqrt(varB);
      var dimensions = [
        { dimension: "平均评分", company_a_value: Math.round(meanA * 100) / 100, company_b_value: Math.round(meanB * 100) / 100, diff: Math.round((meanA - meanB) * 100) / 100, winner: meanA > meanB ? "a" : meanB > meanA ? "b" : "tie" },
        { dimension: "作品数量", company_a_value: sa.length, company_b_value: sb.length, diff: sa.length - sb.length, winner: sa.length > sb.length ? "a" : sb.length > sa.length ? "b" : "tie" },
        { dimension: "标准差", company_a_value: Math.round(stdA * 100) / 100, company_b_value: Math.round(stdB * 100) / 100, diff: Math.round((stdA - stdB) * 100) / 100, winner: stdA < stdB ? "a" : stdB < stdA ? "b" : "tie" },
        { dimension: "最高分", company_a_value: Math.round(Math.max.apply(null, sa) * 100) / 100, company_b_value: Math.round(Math.max.apply(null, sb) * 100) / 100, diff: Math.round((Math.max.apply(null, sa) - Math.max.apply(null, sb)) * 100) / 100, winner: Math.max.apply(null, sa) > Math.max.apply(null, sb) ? "a" : Math.max.apply(null, sb) > Math.max.apply(null, sa) ? "b" : "tie" },
        { dimension: "最低分", company_a_value: Math.round(Math.min.apply(null, sa) * 100) / 100, company_b_value: Math.round(Math.min.apply(null, sb) * 100) / 100, diff: Math.round((Math.min.apply(null, sa) - Math.min.apply(null, sb)) * 100) / 100, winner: Math.min.apply(null, sa) > Math.min.apply(null, sb) ? "a" : Math.min.apply(null, sb) > Math.min.apply(null, sa) ? "b" : "tie" },
      ];

      return {
        cohens_d: cohensD,
        company_a_name: ca.name, company_b_name: cb.name,
        dimensions: dimensions,
        volatility_a: Math.round(stdA * 100) / 100,
        volatility_b: Math.round(stdB * 100) / 100,
      };
    });
  },
};
