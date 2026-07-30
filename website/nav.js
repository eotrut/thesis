/* ==========================================================================
   AURA — Shared Navbar + Backend API helper
   Renders the top navigation into <div id="navbar"></div> and highlights
   the current page based on <body data-page="...">.
   Also exposes window.AURA.api* helpers used by the dashboard, camera view,
   and color-recommendation pages to talk to the Python backend.
   ========================================================================== */

(function () {
  /* ---------------------------------------------------------------------- */
  /* Backend API base                                                        */
  /*                                                                         */
  /* Pages can be opened three ways:                                         */
  /*   1. served by the Flask backend  -> http://localhost:5000/index.html   */
  /*      (same origin, so a relative path works)                            */
  /*   2. straight off disk            -> file:///.../website/index.html     */
  /*      (needs the absolute backend URL; the backend sends CORS headers)    */
  /*   3. served by a SEPARATE static server, e.g. `python -m http.server`   */
  /*      on :8000 — same origin has no /api routes, so the relative path    */
  /*      404s and every call fails. This case cannot be detected from the   */
  /*      URL alone, so verifyApiBase() probes /api/status once at startup    */
  /*      and falls back to the default backend port if the probe fails.      */
  /*                                                                         */
  /* Override the port with ?api=http://localhost:5050 — it is remembered in  */
  /* localStorage so you only need to pass it once.                          */
  /* ---------------------------------------------------------------------- */

  var DEFAULT_API_BASE = "http://localhost:5000";

  function resolveApiBase() {
    var override = null;
    try {
      var params = new URLSearchParams(window.location.search);
      if (params.get("api")) {
        override = params.get("api").replace(/\/$/, "");
        localStorage.setItem("aura.apiBase", override);
      } else {
        override = localStorage.getItem("aura.apiBase");
      }
    } catch (e) {
      /* private mode / no storage — fall through to defaults */
    }

    if (override) return { base: override, explicit: true };
    if (window.location.protocol === "file:") return { base: DEFAULT_API_BASE, explicit: true };
    return { base: "", explicit: false }; // assume same origin, but verify below
  }

  var resolved = resolveApiBase();
  var API_BASE = resolved.base;

  function apiUrl(path) {
    if (path.charAt(0) !== "/") path = "/" + path;
    return API_BASE + path;
  }

  /* Probe the assumed base once. If a same-origin guess turns out to have no
     API behind it (static file server), retarget to the default backend port
     before any real request goes out. Resolves to the base that worked, or the
     original guess if nothing responded — callers still get a clear error. */
  function verifyApiBase() {
    if (resolved.explicit) return Promise.resolve(API_BASE);

    function probe(base) {
      return fetch(base + "/api/status", { method: "GET" })
        .then(function (r) { return r.ok ? base : Promise.reject(new Error("not ok")); });
    }

    return probe(API_BASE)
      .catch(function () {
        // Same origin has no API. Try the conventional backend port instead,
        // unless that is where we already are.
        if (window.location.origin === DEFAULT_API_BASE) throw new Error("no api");
        return probe(DEFAULT_API_BASE).then(function (base) {
          API_BASE = base;
          window.AURA.apiBase = base;
          console.info(
            "[AURA] No API on " + window.location.origin +
            " — using the backend at " + base + " instead."
          );
          return base;
        });
      })
      .catch(function () {
        return API_BASE; // nothing reachable; let the real call report it
      });
  }

  var ready = null;
  function whenReady() {
    if (!ready) ready = verifyApiBase();
    return ready;
  }

  /** fetch() against the backend, with a timeout and JSON parsing. */
  function apiFetch(path, options) {
    options = options || {};
    var timeoutMs = options.timeoutMs || 30000;
    var controller = new AbortController();
    var timer = setTimeout(function () {
      controller.abort();
    }, timeoutMs);

    // Wait for the base-URL probe so the very first call already points at a
    // backend that exists, rather than failing once and self-correcting after.
    return whenReady()
      .then(function () {
        return fetch(apiUrl(path), {
          method: options.method || "GET",
          body: options.body,
          signal: controller.signal
        });
      })
      .then(function (response) {
        clearTimeout(timer);
        return response.json().then(
          function (data) {
            if (!response.ok && !data.error) {
              data.error = "Backend returned HTTP " + response.status;
            }
            data.httpStatus = response.status;
            return data;
          },
          function () {
            throw new Error("Backend returned a non-JSON response (HTTP " + response.status + ")");
          }
        );
      })
      .catch(function (err) {
        clearTimeout(timer);
        if (err.name === "AbortError") {
          throw new Error("Request timed out after " + Math.round(timeoutMs / 1000) + "s.");
        }
        if (err instanceof TypeError) {
          // Network-level failure: server down, wrong port, or blocked by CORS.
          throw new Error(
            "Cannot reach the AURA backend at " + (API_BASE || window.location.origin) +
            ". Start it with `python backend/app.py`."
          );
        }
        throw err;
      });
  }

  /** Turn a base64 JPEG payload from the API into an <img>-ready data URI. */
  function toDataUri(base64, format) {
    if (!base64) return "";
    if (base64.indexOf("data:") === 0) return base64;
    return "data:image/" + (format || "jpeg") + ";base64," + base64;
  }

  var pages = [
    { href: "index.html", label: "Home", id: "index" },
    { href: "dashboard.html", label: "Dashboard", id: "dashboard" },
    { href: "color-recommendation.html", label: "Color Recommendation", id: "color-recommendation" },
    { href: "camera-view.html", label: "Camera View", id: "camera-view" },
    { href: "results.html", label: "Results", id: "results" },
    { href: "about.html", label: "About", id: "about" }
  ];

  function renderNavbar() {
    var mount = document.getElementById("navbar");
    if (!mount) return;

    var currentPage = document.body.getAttribute("data-page") || "";

    var linksHtml = pages
      .map(function (page) {
        var activeClass = page.id === currentPage ? " active" : "";
        return (
          '<a href="' + page.href + '" class="' + activeClass.trim() + '">' +
          page.label +
          "</a>"
        );
      })
      .join("");

    mount.innerHTML =
      '<nav class="navbar">' +
      '<div class="navbar-inner">' +
      '<a href="index.html" class="navbar-logo"><span class="dot"></span>AURA</a>' +
      '<ul class="navbar-links" id="navbar-links">' +
      linksHtml +
      "</ul>" +
      '<button class="navbar-toggle" id="navbar-toggle" aria-label="Toggle navigation">☰</button>' +
      "</div>" +
      "</nav>";

    var toggle = document.getElementById("navbar-toggle");
    var links = document.getElementById("navbar-links");
    if (toggle && links) {
      toggle.addEventListener("click", function () {
        links.classList.toggle("is-open");
      });
    }
  }

  function renderFooter() {
    var mount = document.getElementById("footer");
    if (!mount) return;
    mount.innerHTML =
      '<footer class="site-footer">' +
      "<p>AURA — AI-Based Autonomous Wall Painting Robot &middot; " +
      "Bachelor of Science in Computer Engineering &middot; Holy Angel University, Angeles City, Pampanga, Philippines</p>" +
      "</footer>";
  }

  function showToast(message) {
    var existing = document.querySelector(".toast");
    if (existing) existing.remove();

    var toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    document.body.appendChild(toast);

    requestAnimationFrame(function () {
      toast.classList.add("is-visible");
    });

    setTimeout(function () {
      toast.classList.remove("is-visible");
      setTimeout(function () {
        toast.remove();
      }, 250);
    }, 2600);
  }

  window.AURA = window.AURA || {};
  window.AURA.showToast = showToast;
  window.AURA.apiBase = API_BASE;
  window.AURA.apiUrl = apiUrl;
  window.AURA.apiFetch = apiFetch;
  window.AURA.toDataUri = toDataUri;
  /* Resolves once the API base has been verified. apiFetch() awaits this
     internally; anything that builds a URL by hand (the MJPEG <img> src) must
     await it explicitly, or it will bake in an unverified base. */
  window.AURA.ready = whenReady;

  document.addEventListener("DOMContentLoaded", function () {
    renderNavbar();
    renderFooter();
  });
})();
