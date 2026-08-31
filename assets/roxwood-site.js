/* ============================================================
   OIL ROXWOOD — VITRINE (index.html)
   · thème jour / nuit
   · hero animé : raffinerie, torchères, derricks, palmiers, mer de pétrole
   · simulateur de paie
   · mur de clients, révélations au défilement
   ============================================================ */
(function () {
  "use strict";
  var reduit = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (s) { return document.querySelector(s); };

  /* ---------- THÈME ---------- */
  window.toggleTheme = function () {
    var dark = document.documentElement.classList.toggle("dark");
    try { localStorage.setItem("orx_theme", dark ? "dark" : "light"); } catch (e) {}
    var b = document.getElementById("themeBtn");
    if (b) b.textContent = dark ? "☀️" : "🌙";
  };
  (function () {
    var b = document.getElementById("themeBtn");
    if (b) b.textContent = document.documentElement.classList.contains("dark") ? "☀️" : "🌙";
  })();

  /* ---------- NAVIGATION ---------- */
  var liens = document.querySelector(".nav-links");
  var burger = document.querySelector(".burger");
  if (burger) burger.addEventListener("click", function () {
    var o = liens.classList.toggle("open");
    burger.setAttribute("aria-expanded", String(o));
  });
  document.querySelectorAll(".nav-links a").forEach(function (a) {
    a.addEventListener("click", function () {
      liens.classList.remove("open");
      if (burger) burger.setAttribute("aria-expanded", "false");
    });
  });

  var barre = document.querySelector("nav.barre"), jauge = document.getElementById("pipeline");
  function auScroll() {
    var y = scrollY, h = document.documentElement.scrollHeight - innerHeight;
    if (barre) barre.classList.toggle("collee", y > 50);
    if (jauge) jauge.style.width = (h > 0 ? (y / h) * 100 : 0) + "%";
  }
  addEventListener("scroll", auScroll, { passive: true });
  auScroll();

  /* ---------- RÉVÉLATIONS ---------- */
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("vue"); io.unobserve(e.target); } });
  }, { threshold: .12, rootMargin: "0px 0px -6% 0px" });
  document.querySelectorAll(".rev").forEach(function (el, i) {
    el.style.transitionDelay = (Math.min(i % 4, 3) * 80) + "ms";
    io.observe(el);
  });

  /* ---------- PLAQUES INCLINABLES ---------- */
  if (window.Roxwood) {
    Roxwood.habiller(document, {
      tilt: ".card,.step,.org-card,.hero-stats > div,.simu,.conditions li,.discord-card,.contact-chip",
      rivets: ".simu,.discord-card,.hero-stats > div"
    });
  }

  /* ---------- MUR DES CLIENTS : boucle infinie ---------- */
  (function () { var t = document.getElementById("cliTrack"); if (t) t.innerHTML += t.innerHTML; })();

  /* ---------- SIMULATEUR DE PAIE ----------
     Règles réelles Oil Roxwood : prime = barils × multiplicateur,
     plafonnée à 42 500 $, et versée uniquement si le quota est atteint. */
  (function () {
    var GR = [
      { nom: "Intérimaire", quota: 3000, mult: 1 },
      { nom: "Raffineur",   quota: 3000, mult: 1.5 },
      { nom: "Confirmé",    quota: 5000, mult: 2 },
      { nom: "Expert",      quota: 6500, mult: 2.5 }
    ];
    var CAP = 42500, gi = 3;
    var F = function (n) { return Math.round(n).toLocaleString("fr-FR"); };
    var g = $("#simuGrades"), rg = $("#simuRange"),
        bEl = $("#simuBarils"), pEl = $("#simuPrime"),
        mEl = $("#simuMult"), nEl = $("#simuNote");
    if (!g || !rg) return;

    g.innerHTML = GR.map(function (x, i) {
      return '<button type="button" data-i="' + i + '" class="' + (i === gi ? "on" : "") + '">' + x.nom + "</button>";
    }).join("");

    function calc() {
      var b = +rg.value, gr = GR[gi];
      bEl.textContent = F(b);
      mEl.textContent = "×" + gr.mult;
      if (b < gr.quota) {
        pEl.textContent = "0 $";
        nEl.innerHTML = "❌ Quota non atteint — il te faut <b>" + F(gr.quota) + "</b> barils minimum en " + gr.nom + " pour toucher ta prime.";
      } else {
        var brut = b * gr.mult, prime = Math.min(brut, CAP);
        pEl.textContent = F(prime) + " $";
        nEl.innerHTML = prime >= CAP
          ? "🔝 Plafond atteint (" + F(CAP) + " $) — tu cartonnes ! " + (brut > CAP ? "(" + F(brut) + " $ avant plafond)" : "")
          : "✅ " + F(b) + " barils × " + gr.mult + " = <b>" + F(prime) + " $</b> de prime cette semaine.";
      }
    }
    g.querySelectorAll("button").forEach(function (b) {
      b.onclick = function () {
        gi = +b.dataset.i;
        g.querySelectorAll("button").forEach(function (x) { x.classList.toggle("on", x === b); });
        calc();
      };
    });
    rg.addEventListener("input", calc);
    calc();
  })();

  /* ============================================================
     HERO — la raffinerie de Roxwood
     ============================================================ */
  var cv = document.getElementById("heroCanvas");
  if (!cv) return;
  var cx = cv.getContext("2d");
  var hero = document.getElementById("accueil");
  var W = 0, H = 0, plan = null, etoiles = [], palmiers = [], raf = 0, visible = true;

  var PAL = {
    nuit: {
      ciel: [[0, "#160E1F"], [.28, "#3A1A22"], [.55, "#8C3418"], [.78, "#D9631A"], [.94, "#F0A62A"], [1, "#FBD07A"]],
      soleil: "#FFE6AE", encre: "#0E0907", sol: ["#130E0A", "#0C0907", "#0A0806"],
      etoiles: true, palme: "rgba(255,45,149,.85)", palmeGlow: "rgba(255,45,149,.9)", feu: 1,
      vagues: [["rgba(37,52,77,.55)", "rgba(20,29,45,.9)", null],
               ["rgba(232,160,32,.20)", "rgba(120,80,16,.12)", "rgba(232,160,32,.55)"],
               ["rgba(10,14,22,.92)", "rgba(6,9,14,.98)", "rgba(232,160,32,.25)"]]
    },
    jour: {
      ciel: [[0, "#7FA8CC"], [.35, "#B8C9D6"], [.62, "#E3CDA8"], [.85, "#F0C070"], [1, "#F7DDA6"]],
      soleil: "#FFF6DC", encre: "#3A2A1E", sol: ["#C9B79E", "#B8A388", "#A89377"],
      etoiles: false, palme: "rgba(196,60,120,.7)", palmeGlow: "rgba(196,60,120,.35)", feu: .38,
      vagues: [["rgba(120,132,150,.45)", "rgba(88,98,116,.75)", null],
               ["rgba(201,122,12,.22)", "rgba(150,100,30,.14)", "rgba(201,122,12,.5)"],
               ["rgba(58,42,30,.85)", "rgba(40,29,20,.95)", "rgba(201,122,12,.3)"]]
    }
  };
  function pal() { return document.documentElement.classList.contains("dark") ? PAL.nuit : PAL.jour; }

  function generer() {
    var s = 20260831;
    function rnd() { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; }
    var out = [], x = -40;
    while (x < 1400) {
      var t = rnd(), e;
      if (t < .26)      e = { k: "col",    w: 26 + rnd() * 26, h: 120 + rnd() * 150 };
      else if (t < .46) e = { k: "cuve",   w: 74 + rnd() * 60, h: 44 + rnd() * 30 };
      else if (t < .60) e = { k: "sphere", w: 54 + rnd() * 24, h: 0 };
      else if (t < .74) e = { k: "torche", w: 16,              h: 190 + rnd() * 90 };
      else if (t < .88) e = { k: "rack",   w: 90 + rnd() * 90, h: 34 + rnd() * 26 };
      else              e = { k: "tour",   w: 46 + rnd() * 18, h: 96 + rnd() * 70 };
      e.x = x; e.r = rnd(); out.push(e); x += e.w + 12 + rnd() * 26;
    }
    return out;
  }
  function taille() {
    var dpr = Math.min(devicePixelRatio || 1, 2), r = cv.getBoundingClientRect();
    W = Math.max(320, r.width); H = Math.max(400, r.height);
    cv.width = W * dpr; cv.height = H * dpr;
    cx.setTransform(dpr, 0, 0, dpr, 0, 0);
    plan = generer();
    var R = Math.random;
    etoiles = Array.from({ length: Math.min(110, W / 12 | 0) }, function () {
      return { x: R() * W, y: R() * H * .55, r: R() * 1.4 + .4, tw: R() * 6.28, ts: .01 + R() * .03 };
    });
    /* clin d'œil GTA6 : palmiers néon de Leonida 🌴 */
    palmiers = [{ x: W * .09, s: .9 }, { x: W * .43, s: .7 }, { x: W * .95, s: 1 }];
  }

  function panache(x, y, t, f) {
    for (var i = 0; i < 5; i++) {
      var p = (t * .3 + i * .2) % 1, yy = y - p * 130 * f, rr = (10 + p * 44) * f, a = (1 - p) * .2;
      var dx = x + Math.sin(p * 5 + i) * 16;
      var g = cx.createRadialGradient(dx, yy, 0, dx, yy, rr);
      g.addColorStop(0, "rgba(255,206,150," + a.toFixed(3) + ")");
      g.addColorStop(1, "rgba(255,206,150,0)");
      cx.fillStyle = g; cx.beginPath(); cx.arc(dx, yy, rr, 0, 7); cx.fill();
    }
  }

  function palmier(x, base, s, sway, P) {
    cx.save(); cx.translate(x, base); cx.scale(s, s);
    cx.strokeStyle = P.palme; cx.lineWidth = 3; cx.lineCap = "round";
    cx.shadowColor = P.palmeGlow; cx.shadowBlur = 12;
    cx.beginPath(); cx.moveTo(0, 0); cx.quadraticCurveTo(6, -28, 14 + sway, -52); cx.stroke();
    var tx = 14 + sway, ty = -52;
    for (var a = 0; a < 6; a++) {
      var ang = -2.7 + a * .52;
      cx.beginPath(); cx.moveTo(tx, ty);
      cx.quadraticCurveTo(tx + Math.cos(ang) * 16, ty + Math.sin(ang) * 16 - 6,
                          tx + Math.cos(ang) * 30, ty + Math.sin(ang) * 30 + 7);
      cx.stroke();
    }
    cx.shadowBlur = 0; cx.restore();
  }

  function vague(base, amp, freq, speed, t, c1, c2, edge) {
    cx.beginPath(); cx.moveTo(0, H);
    for (var x = 0; x <= W; x += 6) {
      var y = base + Math.sin(x * freq + t * speed) * amp + Math.sin(x * freq * .37 + t * speed * 1.6) * amp * .5;
      cx.lineTo(x, y);
    }
    cx.lineTo(W, H); cx.closePath();
    var g = cx.createLinearGradient(0, base - amp * 2, 0, H);
    g.addColorStop(0, c1); g.addColorStop(1, c2);
    cx.fillStyle = g; cx.fill();
    if (edge) {
      cx.beginPath();
      for (var x2 = 0; x2 <= W; x2 += 6) {
        var y2 = base + Math.sin(x2 * freq + t * speed) * amp + Math.sin(x2 * freq * .37 + t * speed * 1.6) * amp * .5;
        x2 === 0 ? cx.moveTo(x2, y2) : cx.lineTo(x2, y2);
      }
      cx.strokeStyle = edge; cx.lineWidth = 2; cx.stroke();
    }
  }

  function pompe(t, hz, P) {
    var s = Math.max(.5, Math.min(.92, W / 1500));
    var bx = W * (W < 760 ? .70 : .845), by = hz + 14 * s;
    cx.save(); cx.translate(bx, by); cx.scale(s, s);
    cx.fillStyle = P.encre; cx.strokeStyle = P.encre; cx.lineCap = "round";
    cx.fillRect(-160, -14, 320, 16);
    cx.lineWidth = 13;
    cx.beginPath(); cx.moveTo(-34, 0); cx.lineTo(0, -122); cx.moveTo(34, 0); cx.lineTo(0, -122); cx.stroke();
    cx.lineWidth = 7; cx.beginPath(); cx.moveTo(-22, -44); cx.lineTo(22, -44); cx.stroke();
    var a = Math.sin(t * 1.05) * .2;
    cx.save(); cx.translate(0, -122); cx.rotate(a);
    cx.lineWidth = 17; cx.beginPath(); cx.moveTo(-96, 0); cx.lineTo(120, 0); cx.stroke();
    cx.beginPath(); cx.moveTo(112, -12); cx.quadraticCurveTo(160, -6, 152, 34); cx.lineTo(120, 22); cx.closePath(); cx.fill();
    cx.restore();
    var cxp = -104, cyp = -66, r = 40, ang = t * 1.05 + Math.PI / 2;
    cx.lineWidth = 9;
    cx.beginPath(); cx.moveTo(cxp, 0); cx.lineTo(cxp, cyp); cx.stroke();
    cx.beginPath(); cx.arc(cxp, cyp, 13, 0, 7); cx.fill();
    var px = cxp + Math.cos(ang) * r, py = cyp + Math.sin(ang) * r;
    cx.save(); cx.translate(cxp, cyp); cx.rotate(ang);
    cx.fillRect(-9, -r - 8, 18, r * 2 + 16);
    cx.beginPath(); cx.arc(0, r, 17, 0, 7); cx.fill();
    cx.restore();
    var ex = Math.cos(a) * -96, ey = -122 + Math.sin(a) * -96;
    cx.lineWidth = 8; cx.beginPath(); cx.moveTo(px, py); cx.lineTo(ex, ey); cx.stroke();
    cx.lineWidth = 6;
    cx.beginPath(); cx.moveTo(150, -122 + Math.sin(a) * 120 + 30); cx.lineTo(150, -10); cx.stroke();
    cx.fillRect(132, -14, 36, 16);
    cx.restore();
  }

  function trame(t) {
    var P = pal();
    var hz = H * (W < 760 ? .90 : .775);

    var g = cx.createLinearGradient(0, 0, 0, hz);
    P.ciel.forEach(function (s) { g.addColorStop(s[0], s[1]); });
    cx.fillStyle = g; cx.fillRect(0, 0, W, hz + 2);

    if (P.etoiles) {
      etoiles.forEach(function (st) {
        st.tw += st.ts;
        var b = (Math.sin(st.tw) + 1) / 2;
        cx.beginPath(); cx.arc(st.x, st.y, st.r, 0, 7);
        cx.fillStyle = "rgba(255,235,190," + (.08 + .5 * b).toFixed(3) + ")"; cx.fill();
      });
    }

    var sx = W * .6, sy = hz - 14 + Math.sin(t * .08) * 3, R = Math.max(46, W * .055);
    var halo = cx.createRadialGradient(sx, sy, 0, sx, sy, R * 6);
    halo.addColorStop(0, "rgba(255,214,130,.85)");
    halo.addColorStop(.18, "rgba(255,163,60,.42)");
    halo.addColorStop(.52, "rgba(217,90,26,.16)");
    halo.addColorStop(1, "rgba(217,90,26,0)");
    cx.fillStyle = halo; cx.beginPath(); cx.arc(sx, sy, R * 6, 0, 7); cx.fill();
    cx.fillStyle = P.soleil; cx.beginPath(); cx.arc(sx, sy, R, 0, 7); cx.fill();

    for (var i = 0; i < 7; i++) {
      var by = hz - 40 - i * 34 - (i % 2) * 12;
      var dx = ((t * (5 + i * 2.4)) % (W + 700)) - 350;
      var bg = cx.createLinearGradient(dx - 260, 0, dx + 260, 0);
      bg.addColorStop(0, "rgba(28,14,10,0)");
      bg.addColorStop(.5, "rgba(28,14,10," + (.2 + i * .045).toFixed(2) + ")");
      bg.addColorStop(1, "rgba(28,14,10,0)");
      cx.fillStyle = bg; cx.beginPath(); cx.ellipse(dx, by, 250 + i * 34, 6 + i * 1.6, 0, 0, 7); cx.fill();
    }

    var kx = W / 1150, ky = Math.max(.26, Math.min(.62, kx * .52));
    plan.forEach(function (e) {
      var x = e.x * kx, w = e.w * ky, h = e.h * ky;
      if (e.k === "col" && e.r > .45) panache(x + w / 2, hz - h, t + e.r * 4, .7);
      if (e.k === "tour") panache(x + w / 2, hz - h, t + e.r * 6, 1);
    });

    palmiers.forEach(function (p, i) { palmier(p.x, hz, p.s, Math.sin(t * .8 + i * 2) * 2.2, P); });

    cx.fillStyle = P.encre; cx.strokeStyle = P.encre;
    plan.forEach(function (e) {
      var x = e.x * kx, w = e.w * ky, h = e.h * ky, y, xx;
      cx.beginPath();
      if (e.k === "col") {
        cx.rect(x, hz - h, w, h); cx.rect(x - 4, hz - h - 6, w + 8, 7); cx.fill();
        cx.lineWidth = 2;
        for (y = hz - h + 16; y < hz - 10; y += 22) { cx.beginPath(); cx.moveTo(x - 3, y); cx.lineTo(x + w + 3, y); cx.stroke(); }
      } else if (e.k === "cuve") {
        cx.rect(x, hz - h, w, h); cx.ellipse(x + w / 2, hz - h, w / 2, 7, 0, 0, 7); cx.fill();
      } else if (e.k === "sphere") {
        var r = w / 2.4;
        cx.arc(x + w / 2, hz - r - 16, r, 0, 7); cx.fill();
        cx.lineWidth = 3; cx.beginPath();
        cx.moveTo(x + w / 2 - r * .7, hz - 16); cx.lineTo(x + w / 2 - r * .5, hz);
        cx.moveTo(x + w / 2 + r * .7, hz - 16); cx.lineTo(x + w / 2 + r * .5, hz); cx.stroke();
      } else if (e.k === "torche") {
        cx.rect(x + w * .3, hz - h, w * .4, h); cx.fill();
        cx.lineWidth = 1.6;
        for (y = hz - h; y < hz; y += 16) {
          cx.beginPath(); cx.moveTo(x, y + 8); cx.lineTo(x + w, y); cx.moveTo(x, y); cx.lineTo(x + w, y + 8); cx.stroke();
        }
        var fl = 16 + Math.sin(t * 6 + e.r * 9) * 5 + Math.sin(t * 17 + e.r) * 3;
        var F = P.feu;
        var fg = cx.createRadialGradient(x + w / 2, hz - h - fl * .6, 0, x + w / 2, hz - h - fl * .6, fl * 3.4);
        fg.addColorStop(0, "rgba(255,236,190," + (.95 * F).toFixed(2) + ")");
        fg.addColorStop(.3, "rgba(255,150,40," + (.65 * F).toFixed(2) + ")");
        fg.addColorStop(1, "rgba(255,90,20,0)");
        cx.fillStyle = fg; cx.beginPath(); cx.arc(x + w / 2, hz - h - fl * .6, fl * 3.4, 0, 7); cx.fill();
        cx.fillStyle = "#FFD79A"; cx.beginPath();
        cx.moveTo(x + w * .34, hz - h);
        cx.quadraticCurveTo(x + w / 2 - 5, hz - h - fl, x + w / 2, hz - h - fl * 1.7);
        cx.quadraticCurveTo(x + w / 2 + 6, hz - h - fl, x + w * .66, hz - h);
        cx.fill(); cx.fillStyle = P.encre;
      } else if (e.k === "rack") {
        cx.rect(x, hz - h, w, 8); cx.rect(x, hz - h + 14, w, 5); cx.fill();
        cx.lineWidth = 4;
        for (xx = x + 8; xx < x + w; xx += 30) { cx.beginPath(); cx.moveTo(xx, hz - h); cx.lineTo(xx, hz); cx.stroke(); }
      } else {
        cx.moveTo(x, hz);
        cx.bezierCurveTo(x + w * .22, hz - h * .55, x + w * .28, hz - h * .7, x + w * .3, hz - h);
        cx.lineTo(x + w * .7, hz - h);
        cx.bezierCurveTo(x + w * .72, hz - h * .7, x + w * .78, hz - h * .55, x + w, hz);
        cx.closePath(); cx.fill();
      }
    });

    var sol = cx.createLinearGradient(0, hz, 0, H);
    sol.addColorStop(0, P.sol[0]); sol.addColorStop(.35, P.sol[1]); sol.addColorStop(1, P.sol[2]);
    cx.fillStyle = sol; cx.fillRect(0, hz, W, H - hz);

    pompe(t, hz, P);

    /* mer de pétrole au premier plan */
    var v = P.vagues;
    vague(H * .93, 12, .006, .9, t, v[0][0], v[0][1], v[0][2]);
    vague(H * .955, 14, .0045, -.7, t, v[1][0], v[1][1], v[1][2]);
    vague(H * .985, 10, .007, 1.15, t, v[2][0], v[2][1], v[2][2]);
  }

  var t0 = performance.now();
  function boucle(now) { raf = 0; trame((now - t0) / 1000); if (!reduit && visible && !document.hidden) raf = requestAnimationFrame(boucle); }
  function jouer() { if (raf || reduit || !visible) return; raf = requestAnimationFrame(boucle); }
  function stopper() { if (raf) { cancelAnimationFrame(raf); raf = 0; } }
  function demarrer() { stopper(); taille(); reduit ? trame(2.4) : jouer(); }

  addEventListener("resize", function () { clearTimeout(window.__rz); window.__rz = setTimeout(demarrer, 180); });
  document.addEventListener("visibilitychange", function () { document.hidden ? stopper() : jouer(); });
  new IntersectionObserver(function (es) { visible = es[0].isIntersecting; visible ? jouer() : stopper(); }, { threshold: 0 }).observe(cv);

  /* repeint immédiatement au changement de thème */
  new MutationObserver(function () { if (reduit) trame(2.4); }).observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

  demarrer();
})();
