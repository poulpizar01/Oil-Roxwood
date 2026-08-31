/* ============================================================
   OIL ROXWOOD — COMPORTEMENTS COMMUNS
   Chargé par index.html ET admin.html.
   · lampe torche qui suit le curseur et révèle la rouille
   · plaques inclinables en 3D + reflet métallique
   · rivets posés automatiquement sur les plaques
   · bandeau raffinerie animé en fond (admin)
   Aucune dépendance. Ne touche à aucune donnée.
   ============================================================ */
(function (global) {
  "use strict";

  var reduit = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var survol = matchMedia("(hover:hover)").matches && !reduit;

  /* ---------- 1. LAMPE TORCHE ---------- */
  function torche() {
    if (!survol || document.getElementById("torche")) return;
    ["rouille", "torche"].forEach(function (id) {
      var d = document.createElement("div");
      d.id = id;
      d.setAttribute("aria-hidden", "true");
      document.body.appendChild(d);
    });
    var x = -600, y = -600, attente = false, racine = document.documentElement;
    addEventListener("pointermove", function (e) {
      x = e.clientX; y = e.clientY;
      if (attente) return;
      attente = true;
      requestAnimationFrame(function () {
        racine.style.setProperty("--mx", x + "px");
        racine.style.setProperty("--my", y + "px");
        attente = false;
      });
    }, { passive: true });
  }

  /* ---------- 2. PLAQUES INCLINABLES ---------- */
  function brancherTilt(el, force) {
    if (!survol || !el || el.__tilt) return;
    el.__tilt = true;
    var cadre = 0;
    var amp = force || 1;
    el.addEventListener("pointerenter", function () { el.classList.add("actif"); });
    el.addEventListener("pointermove", function (e) {
      if (cadre) return;
      cadre = requestAnimationFrame(function () {
        cadre = 0;
        var r = el.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width;
        var py = (e.clientY - r.top) / r.height;
        el.style.setProperty("--ry", ((px - .5) * 9 * amp).toFixed(2) + "deg");
        el.style.setProperty("--rx", ((.5 - py) * 7 * amp).toFixed(2) + "deg");
        el.style.setProperty("--sx", (px * 100).toFixed(1) + "%");
        el.style.setProperty("--sy", (py * 100).toFixed(1) + "%");
      });
    });
    el.addEventListener("pointerleave", function () {
      el.classList.remove("actif");
      el.style.setProperty("--rx", "0deg");
      el.style.setProperty("--ry", "0deg");
    });
  }

  /* ---------- 3. RIVETS + BRANCHEMENT AUTOMATIQUE ---------- */
  var RIVETS = '<i class="rivet a"></i><i class="rivet b"></i><i class="rivet c"></i><i class="rivet d"></i>';

  /**
   * habiller(racine, options)
   *   options.tilt   : sélecteur des éléments qui pivotent   (petites plaques)
   *   options.lueur  : sélecteur des éléments à reflet seul  (grands panneaux)
   *   options.rivets : sélecteur des éléments à boulonner
   */
  function habiller(racine, o) {
    racine = racine || document;
    o = o || {};
    if (o.rivets) {
      racine.querySelectorAll(o.rivets).forEach(function (el) {
        if (el.__rivets) return;
        el.__rivets = true;
        if (getComputedStyle(el).position === "static") el.style.position = "relative";
        el.insertAdjacentHTML("afterbegin", RIVETS);
      });
    }
    if (o.tilt) {
      racine.querySelectorAll(o.tilt).forEach(function (el) {
        el.setAttribute("data-tilt", "");
        brancherTilt(el, o.amplitude);
      });
    }
    if (o.lueur) {
      racine.querySelectorAll(o.lueur).forEach(function (el) {
        el.setAttribute("data-lueur", "");
        brancherTilt(el, 0);   // reflet seul, aucune rotation
      });
    }
  }

  /** Réapplique `habiller` à chaque fois que le conteneur est re-rendu. */
  function surveiller(cible, o) {
    if (!cible) return;
    habiller(cible, o);
    new MutationObserver(function () { habiller(cible, o); })
      .observe(cible, { childList: true, subtree: true });
  }

  /* ---------- 4. BANDEAU RAFFINERIE (fond de l'admin) ---------- */
  function bandeauRaffinerie(opts) {
    if (reduit) return;
    opts = opts || {};
    var cv = opts.canvas;
    if (cv) {
      cv.style.opacity = (opts.opacite != null ? opts.opacite : .9);
    } else {
      cv = document.createElement("canvas");
      cv.id = "skyline";
      cv.setAttribute("aria-hidden", "true");
      cv.style.cssText = "position:fixed;left:0;right:0;bottom:0;width:100%;height:" +
        (opts.hauteur || 230) + "px;z-index:0;pointer-events:none;opacity:" + (opts.opacite || .5);
      document.body.prepend(cv);
    }

    var c = cv.getContext("2d"), W = 0, H = 0, plan = null, raf = 0;

    function generer() {
      var s = 20260831;
      function rnd() { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; }
      var out = [], x = -60;
      while (x < 1300) {
        var t = rnd(), e;
        if (t < .26)      e = { k: "col",    w: 24 + rnd() * 22, h: 120 + rnd() * 120 };
        else if (t < .46) e = { k: "cuve",   w: 76 + rnd() * 54, h: 42 + rnd() * 24 };
        else if (t < .62) e = { k: "sphere", w: 52 + rnd() * 22, h: 0 };
        else if (t < .78) e = { k: "torche", w: 16,              h: 190 + rnd() * 70 };
        else              e = { k: "rack",   w: 88 + rnd() * 80, h: 34 + rnd() * 20 };
        e.x = x; e.r = rnd(); out.push(e); x += e.w + 14 + rnd() * 30;
      }
      return out;
    }
    function taille() {
      var dpr = Math.min(devicePixelRatio || 1, 2), r = cv.getBoundingClientRect();
      W = Math.max(320, r.width); H = Math.max(120, r.height);
      cv.width = W * dpr; cv.height = H * dpr;
      c.setTransform(dpr, 0, 0, dpr, 0, 0);
      plan = generer();
    }
    function trame(t) {
      c.clearRect(0, 0, W, H);
      var hz = H;
      var kx = W / 1050, ky = Math.max(.26, Math.min(.5, kx * .42));
      var nuit = document.documentElement.classList.contains("dark");
      var encre = nuit ? "#050403" : "#2A1F16";

      /* lueur d'horizon */
      var g = c.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0, "rgba(232,160,32,0)");
      g.addColorStop(1, nuit ? "rgba(232,160,32,.14)" : "rgba(201,122,12,.10)");
      c.fillStyle = g; c.fillRect(0, 0, W, H);

      c.fillStyle = encre; c.strokeStyle = encre;
      plan.forEach(function (e) {
        var x = e.x * kx, w = e.w * ky, h = e.h * ky;
        c.beginPath();
        if (e.k === "col") {
          c.rect(x, hz - h, w, h); c.rect(x - 3, hz - h - 5, w + 6, 6); c.fill();
          c.lineWidth = 2;
          for (var y = hz - h + 14; y < hz - 8; y += 20) {
            c.beginPath(); c.moveTo(x - 2, y); c.lineTo(x + w + 2, y); c.stroke();
          }
        } else if (e.k === "cuve") {
          c.rect(x, hz - h, w, h); c.ellipse(x + w / 2, hz - h, w / 2, 6, 0, 0, 7); c.fill();
        } else if (e.k === "sphere") {
          var r = w / 2.4;
          c.arc(x + w / 2, hz - r - 14, r, 0, 7); c.fill();
          c.lineWidth = 3; c.beginPath();
          c.moveTo(x + w / 2 - r * .7, hz - 14); c.lineTo(x + w / 2 - r * .5, hz);
          c.moveTo(x + w / 2 + r * .7, hz - 14); c.lineTo(x + w / 2 + r * .5, hz); c.stroke();
        } else if (e.k === "torche") {
          c.rect(x + w * .3, hz - h, w * .4, h); c.fill();
          c.lineWidth = 1.4;
          for (var yy = hz - h; yy < hz; yy += 15) {
            c.beginPath(); c.moveTo(x, yy + 7); c.lineTo(x + w, yy);
            c.moveTo(x, yy); c.lineTo(x + w, yy + 7); c.stroke();
          }
          var fl = 12 + Math.sin(t * 6 + e.r * 9) * 4 + Math.sin(t * 15 + e.r) * 2.5;
          var fg = c.createRadialGradient(x + w / 2, hz - h - fl * .6, 0, x + w / 2, hz - h - fl * .6, fl * 3.2);
          fg.addColorStop(0, "rgba(255,232,180,.9)");
          fg.addColorStop(.32, "rgba(255,146,38,.5)");
          fg.addColorStop(1, "rgba(255,90,20,0)");
          c.fillStyle = fg; c.beginPath(); c.arc(x + w / 2, hz - h - fl * .6, fl * 3.2, 0, 7); c.fill();
          c.fillStyle = "#FFD08A"; c.beginPath();
          c.moveTo(x + w * .34, hz - h);
          c.quadraticCurveTo(x + w / 2 - 4, hz - h - fl, x + w / 2, hz - h - fl * 1.7);
          c.quadraticCurveTo(x + w / 2 + 5, hz - h - fl, x + w * .66, hz - h);
          c.fill(); c.fillStyle = encre;
        } else {
          c.rect(x, hz - h, w, 7); c.rect(x, hz - h + 12, w, 4); c.fill();
          c.lineWidth = 3.5;
          for (var xx = x + 7; xx < x + w; xx += 26) {
            c.beginPath(); c.moveTo(xx, hz - h); c.lineTo(xx, hz); c.stroke();
          }
        }
      });
    }
    var t0 = performance.now();
    function boucle(now) { raf = 0; trame((now - t0) / 1000); if (!document.hidden) raf = requestAnimationFrame(boucle); }
    function relancer() { if (raf) cancelAnimationFrame(raf); raf = 0; taille(); raf = requestAnimationFrame(boucle); }
    addEventListener("resize", function () { clearTimeout(cv.__rz); cv.__rz = setTimeout(relancer, 200); });
    document.addEventListener("visibilitychange", function () { if (!document.hidden && !raf) raf = requestAnimationFrame(boucle); });
    relancer();
  }

  /* ---------- 5. RUBAN DÉFILANT ---------- */
  function ruban(el, mots) {
    if (!el) return;
    var bloc = "<div>" + mots.map(function (m) { return "<span>" + m + "</span>"; }).join("") + "</div>";
    el.innerHTML = bloc + bloc;
  }

  global.Roxwood = {
    reduit: reduit,
    survol: survol,
    torche: torche,
    habiller: habiller,
    surveiller: surveiller,
    brancherTilt: brancherTilt,
    bandeauRaffinerie: bandeauRaffinerie,
    ruban: ruban
  };

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", torche);
  else torche();

})(window);
