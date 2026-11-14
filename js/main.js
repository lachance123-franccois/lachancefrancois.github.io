(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* Couleurs des animations : lues dans css/theme.css, pour suivre la palette */
  var rootStyle = getComputedStyle(document.documentElement);
  function cssVar(name, fallback) {
    var v = (rootStyle.getPropertyValue(name) || '').trim();
    return v || fallback;
  }
  var C = {
    vizBg:    cssVar('--viz-bg', '#eaf2fa'),      /* fond clair des vignettes */
    line:     cssVar('--signal-dim', '#0e7490'),  /* tracé normal sur fond clair */
    alert:    cssVar('--detect-dim', '#b45309'),  /* tracé d'alerte sur fond clair */
    scopeBg:  cssVar('--scope-bg', '#071a33'),    /* écran sombre (oscilloscope, radiographie) */
    glow:     cssVar('--signal', '#06b6d4'),      /* tracé normal sur fond sombre */
    glowWarn: cssVar('--detect', '#f59e0b')       /* tracé d'alerte sur fond sombre */
  };

  /* Les scènes sont dessinées à 30 images par seconde : chaque dessin avance de STEP pas */
  var STEP = 2;

  function initNav() {
    var nav = $('#siteNav');
    var toggle = $('#navToggle');
    var menu = $('#navMenu');

    if (nav) {
      var ticking = false;
      window.addEventListener('scroll', function () {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () {
          nav.classList.toggle('is-scrolled', window.scrollY > 24);
          ticking = false;
        });
      }, { passive: true });
    }

    if (!toggle || !menu) return;

    function setOpen(open) {
      menu.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
      toggle.textContent = open ? '✕' : '☰';
    }

    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });

    $$('a', menu).forEach(function (a) {
      a.addEventListener('click', function () { setOpen(false); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  function initToTop() {
    var btn = $('#toTop');
    if (!btn) return;
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        btn.classList.toggle('is-visible', window.scrollY > 500);
        ticking = false;
      });
    }, { passive: true });
    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
    });
  }

  var revealObserver = null;

  function initReveal() {
    var items = $$('.reveal:not(.is-in)');
    if (!items.length) return;

    if (reduceMotion || !('IntersectionObserver' in window)) {
      items.forEach(function (el) { el.classList.add('is-in'); });
      return;
    }

    if (!revealObserver) {
      revealObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          e.target.classList.add('is-in');
          revealObserver.unobserve(e.target);
        });
      }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
    }
    items.forEach(function (el) { revealObserver.observe(el); });
  }

  window.FLReveal = initReveal;

  function createScene(canvas, drawFrame, opts) {
    if (!canvas || !canvas.getContext) return null;
    opts = opts || {};

    var ctx = canvas.getContext('2d', { alpha: false });
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = 0, h = 0, frame = 0, running = false, rafId = null, visible = false, last = 0;

    function fit() {
      var cw = canvas.clientWidth || canvas.offsetWidth;
      var ch = canvas.clientHeight || canvas.offsetHeight;
      if (!cw || !ch) return false;
      if (cw === w && ch === h) return true;
      w = cw; h = ch;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return true;
    }

    function loop(ts) {
      if (!running) return;
      rafId = requestAnimationFrame(loop);
      if (ts - last < 30) return;
      last = ts;
      if (fit()) { drawFrame(ctx, w, h, frame); frame += STEP; }
    }

    function start() {
      if (running) return;
      running = true;
      rafId = requestAnimationFrame(loop);
    }
    function stop() {
      running = false;
      if (rafId) cancelAnimationFrame(rafId);
      rafId = null;
    }

    function renderStill() {
      if (fit()) drawFrame(ctx, w, h, opts.stillFrame || 0);
    }

    if (reduceMotion) {
      requestAnimationFrame(renderStill);
      window.addEventListener('resize', function () { w = 0; renderStill(); });
      return { start: function () {}, stop: function () {} };
    }

    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        visible = entries[0].isIntersecting;
        if (visible && !document.hidden) start(); else stop();
      }, { threshold: 0.05 }).observe(canvas);
    } else {
      visible = true;
      start();
    }

    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop(); else if (visible) start();
    });

    return { start: start, stop: stop };
  }

  window.FLScene = createScene;

  function initHeroScope() {
    var canvas = $('#heroScope');
    if (!canvas) return;

    var elState = $('#scopeState'), elSnr = $('#scopeSnr'),
        elLat   = $('#scopeLat'),   elDec = $('#scopeDec');

    var BUF = 340, buf = [], t = 0, lastLabel = '';
    var PHASES = [
      { name: 'acquisition', until: 240, snr: '4.2 dB',  lat: '…',     dec: 'en attente' },
      { name: 'filtrage',    until: 480, snr: '11.6 dB', lat: '8 ms',  dec: 'en attente' },
      { name: 'détection',   until: 700, snr: '11.6 dB', lat: '23 ms', dec: 'crise' }
    ];

    function phaseAt(f) {
      var m = f % 700;
      for (var i = 0; i < PHASES.length; i++) if (m < PHASES[i].until) return PHASES[i];
      return PHASES[0];
    }

    function sample(t, phase) {
      var clean = Math.sin(t * 0.08) * 0.34 + Math.sin(t * 0.21) * 0.14 + Math.sin(t * 0.53) * 0.07;
      if (phase.name === 'acquisition') return clean + (Math.random() - 0.5) * 0.55;
      if (phase.name === 'filtrage')    return clean + (Math.random() - 0.5) * 0.06;
      return Math.sin(t * 0.5) * 0.3 + Math.sin(t * 1.7) * 0.55
           + Math.sin(t * 3.0) * 0.3 + (Math.random() - 0.5) * 0.16;
    }

    createScene(canvas, function (ctx, w, h, f) {
      var phase = phaseAt(f);

      if (phase.name !== lastLabel) {
        lastLabel = phase.name;
        if (elState) elState.textContent = phase.name;
        if (elSnr)   elSnr.textContent   = phase.snr;
        if (elLat)   elLat.textContent   = phase.lat;
        if (elDec)   elDec.textContent   = phase.dec;
      }

      for (var k = 0; k < STEP; k++) {
        buf.push(sample(t, phase));
        if (buf.length > BUF) buf.shift();
        t += 0.6;
      }

      ctx.fillStyle = C.scopeBg;
      ctx.fillRect(0, 0, w, h);

      ctx.strokeStyle = 'rgba(6,182,212,0.10)';
      ctx.lineWidth = 1;
      for (var x = 0; x <= w; x += 44) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
      for (var y = 0; y <= h; y += 34) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }

      var isDetect = phase.name === 'détection';
      var color = isDetect ? C.glowWarn : C.glow;

      if (isDetect) {
        ctx.fillStyle = 'rgba(245,158,11,' + (0.05 + 0.04 * Math.sin(f * 0.25)) + ')';
        ctx.fillRect(0, 0, w, h);
      }

      var mid = h / 2, amp = h * 0.3;
      ctx.beginPath();
      for (var i = 0; i < buf.length; i++) {
        var px = (i / BUF) * w, py = mid - buf[i] * amp;
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.8;
      ctx.stroke();

      if (isDetect) {
        ctx.fillStyle = color;
        ctx.font = '500 12px "IBM Plex Mono", monospace';
        ctx.fillText('crise détectée', 12, 22);
      }
    }, { stillFrame: 300 });
  }

  function initProjectViz() {
    /* Détection d'anomalies : le signal sort de son comportement normal */
    var an = $('#viz-anomaly');
    if (an) {
      var abuf = [], AB = 260, at = 0;
      var anStep = function (drift) {
        at++;
        var s = Math.sin(at * 0.12) * 0.2 + Math.sin(at * 0.34) * 0.1 + (Math.random() - 0.5) * 0.05;
        if (drift) s += Math.sin(at * 0.9) * 0.3 + (Math.random() - 0.5) * 0.4;
        abuf.push(s);
        if (abuf.length > AB) abuf.shift();
      };
      for (var a0 = 0; a0 < AB; a0++) anStep(a0 > AB - 70);
      createScene(an, function (ctx, w, h, f) {
        var drift = (f % 440) > 290;
        for (var k = 0; k < STEP; k++) anStep(drift);

        ctx.fillStyle = C.vizBg; ctx.fillRect(0, 0, w, h);
        var mid = h * 0.56, amp = h * 0.42, lim = 0.42;
        ctx.strokeStyle = 'rgba(15,33,55,0.28)'; ctx.lineWidth = 1; ctx.setLineDash([4, 4]);
        [-1, 1].forEach(function (sg) {
          ctx.beginPath(); ctx.moveTo(0, mid - sg * lim * amp); ctx.lineTo(w, mid - sg * lim * amp); ctx.stroke();
        });
        ctx.setLineDash([]);

        var c = drift ? C.alert : C.line;
        ctx.beginPath();
        for (var i = 0; i < abuf.length; i++) {
          var x = (i / AB) * w, y = mid - Math.max(-1, Math.min(1, abuf[i])) * amp;
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.strokeStyle = c; ctx.lineWidth = 1.5; ctx.stroke();
        ctx.fillStyle = c;
        ctx.font = '500 11px "IBM Plex Mono", monospace';
        ctx.fillText(drift ? 'anomalie' : 'comportement normal', 12, 20);
      }, { stillFrame: 300 });
    }

    /* Audio spatial : un lobe directif pointe tour à tour vers deux voix */
    var am = $('#viz-ambi');
    if (am) {
      createScene(am, function (ctx, w, h, f) {
        var cx = w / 2, cy = h / 2 + 6, R = Math.min(w, h) * 0.36;
        var sa = 0.45, sb = 2.5;
        var steer = sa + (sb - sa) * (0.5 - 0.5 * Math.cos(f / 60 * 0.8));

        ctx.fillStyle = C.vizBg; ctx.fillRect(0, 0, w, h);
        ctx.strokeStyle = 'rgba(15,33,55,0.12)'; ctx.lineWidth = 1;
        [1, 0.5].forEach(function (k) { ctx.beginPath(); ctx.arc(cx, cy, R * k, 0, Math.PI * 2); ctx.stroke(); });
        ctx.beginPath(); ctx.moveTo(cx - R, cy); ctx.lineTo(cx + R, cy); ctx.moveTo(cx, cy - R); ctx.lineTo(cx, cy + R); ctx.stroke();

        ctx.beginPath();
        for (var a = 0; a <= Math.PI * 2 + 0.05; a += 0.05) {
          var r = R * (0.5 + 0.5 * Math.cos(a - steer));
          var px = cx + r * Math.cos(a), py = cy - r * Math.sin(a);
          a === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fillStyle = 'rgba(14,116,144,0.16)'; ctx.fill();
        ctx.strokeStyle = C.line; ctx.lineWidth = 2; ctx.stroke();

        ctx.font = '500 11px "IBM Plex Mono", monospace';
        [[sa, C.line, 'voix A'], [sb, C.alert, 'voix B']].forEach(function (s) {
          var px = cx + R * 1.05 * Math.cos(s[0]), py = cy - R * 1.05 * Math.sin(s[0]);
          ctx.beginPath(); ctx.arc(px, py, 5, 0, Math.PI * 2); ctx.fillStyle = s[1]; ctx.fill();
          ctx.textAlign = Math.cos(s[0]) > 0 ? 'left' : 'right';
          ctx.fillText(s[2], px + (Math.cos(s[0]) > 0 ? 10 : -10), py + 4);
        });
        ctx.textAlign = 'left';
        ctx.fillStyle = C.line;
        ctx.fillText('direction visée', 12, 20);
      }, { stillFrame: 90 });
    }

    var sc = $('#viz-shortcut');
    if (sc) {
      createScene(sc, function (ctx, w, h, f) {
        var cycle = f % 300;
        var glyph = cycle < 90 ? 0
                  : cycle < 150 ? (cycle - 90) / 60
                  : cycle < 240 ? 1
                  : 1 - (cycle - 240) / 60;
        glyph = Math.max(0, Math.min(1, glyph));
        var biased = glyph > 0.5;

        ctx.fillStyle = C.vizBg;
        ctx.fillRect(0, 0, w, h);

        /* film radiographique : panneau sombre centré, marge claire autour */
        var m = Math.round(Math.min(w, h) * 0.09);
        var fw = w - 2 * m, fh = Math.min(h - 2 * m, fw * 1.1);
        var fx = m, fy = (h - fh) / 2;
        ctx.fillStyle = C.scopeBg;
        ctx.fillRect(fx, fy, fw, fh);

        var cx = fx + fw / 2, cy = fy + fh * 0.54, r = Math.min(fw, fh) * 0.34;

        ctx.save();
        ctx.translate(cx, cy);
        ctx.scale(0.86, 1);
        ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(190,205,220,0.34)'; ctx.fill();
        ctx.restore();

        [-1, 1].forEach(function (side) {
          ctx.save();
          ctx.translate(cx + side * r * 0.38, cy - r * 0.06);
          ctx.scale(0.42, 0.78);
          ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(4,14,30,0.88)'; ctx.fill();
          ctx.restore();
        });

        ctx.fillStyle = 'rgba(210,222,232,0.4)';
        ctx.fillRect(cx - 1.5, cy - r * 0.85, 3, r * 1.7);

        if (glyph > 0.01) {
          var gx = fx + 10, gy = fy + 10, gs = Math.min(fw, fh) * 0.14;
          ctx.strokeStyle = 'rgba(255,255,255,' + (0.85 * glyph) + ')';
          ctx.lineWidth = 3;
          ctx.beginPath();
          ctx.moveTo(gx, gy); ctx.lineTo(gx, gy + gs); ctx.lineTo(gx + gs * 0.7, gy + gs);
          ctx.stroke();
        }

        var verdict = biased ? 'malade' : 'sain';
        ctx.fillStyle = biased ? C.glowWarn : C.glow;
        ctx.font = '500 12px "IBM Plex Mono", monospace';
        ctx.textAlign = 'right';
        ctx.fillText('diagnostic : ' + verdict, fx + fw - 12, fy + 22);
        ctx.textAlign = 'left';
        ctx.fillStyle = 'rgba(255,255,255,0.55)';
        ctx.font = '400 10px "IBM Plex Mono", monospace';
        ctx.fillText('poumons inchangés', fx + 12, fy + fh - 12);
      }, { stillFrame: 200 });
    }
  }

  function initForm() {
    var form = $('#contactForm');
    if (!form) return;
    var status = $('#formStatus');
    var submit = form.querySelector('button[type="submit"]');

    function say(msg, ok) {
      if (!status) return;
      status.textContent = msg;
      status.className = 'form-status is-visible ' + (ok ? 'form-status--ok' : 'form-status--fail');
    }

    form.addEventListener('submit', function (e) {
      var action = form.getAttribute('action') || '';
      var notConfigured = !action || /VOTRE_|YOUR_|xxxx|exemple\.|example\./i.test(action);
      if (notConfigured) {
        e.preventDefault();
        say("Le formulaire n'est pas encore relié à un service d'envoi. "
            + 'Écrivez directement à lachanceawounang@icloud.com.', false);
        return;
      }

      e.preventDefault();
      if (form.querySelector('.hp') && form.querySelector('.hp').value) return;

      var original = submit ? submit.textContent : '';
      if (submit) { submit.disabled = true; submit.textContent = 'Envoi en cours…'; }

      fetch(action, {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' }
      })
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          form.reset();
          say('Message reçu. Je réponds sous 24 à 48 heures.', true);
        })
        .catch(function () {
          say("L'envoi a échoué. Si c'est le premier message envoyé depuis ce "
              + 'formulaire, le service attend peut-être une confirmation par email. '
              + 'Sinon, écrivez à lachanceawounang@icloud.com : la réponse sera la même.', false);
        })
        .then(function () {
          if (submit) { submit.disabled = false; submit.textContent = original; }
        });
    });
  }

  function boot() {
    initNav();
    initToTop();
    initReveal();
    initHeroScope();
    initProjectViz();
    initForm();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();