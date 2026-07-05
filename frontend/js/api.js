/**
 * API call layer — simple, robust fetch wrapper.
 */
var ApiError = (function () {
  function ApiError(message, code) {
    this.name = "ApiError";
    this.message = message;
    this.code = code;
  }
  ApiError.prototype = Object.create(Error.prototype);
  ApiError.prototype.constructor = ApiError;
  return ApiError;
})();

var API = {
  BASE: "/api/v1",

  get: function (path) {
    var self = this;
    return fetch(self.BASE + path, {
      headers: { Accept: "application/json" },
    }).then(function (res) {
      if (!res.ok) {
        return res.json().then(function (body) {
          throw new ApiError(body.detail || ("HTTP " + res.status), "HTTP_" + res.status);
        }, function () {
          throw new ApiError("HTTP " + res.status, "HTTP_" + res.status);
        });
      }
      return res.json();
    }).catch(function (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError("Network error", "NETWORK");
    });
  },

  getRaw: function (path) {
    return fetch(this.BASE + path).then(function (res) {
      if (!res.ok) throw new ApiError("HTTP " + res.status, "HTTP_" + res.status);
      return res;
    });
  },
};

/**
 * Show a toast notification.
 */
function showToast(message, type) {
  var toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.className = "toast " + (type || "") + " show";
  setTimeout(function () { toast.classList.remove("show"); }, 3000);
}
