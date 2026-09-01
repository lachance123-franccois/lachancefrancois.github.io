/* ==========================================================================
   main.js — un seul point d'entrée, aucune dépendance externe.
   Corrige : double initialisation, plantage quand un élément est absent,
   effet machine à écrire qui détruisait le H1, compteurs qui bouclaient,
   parallaxe non throttlée, AOS appelé avant chargement.
   ========================================================================== */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- Navigation ------------------------------------------------ */
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

    // Fermer après un clic sur un lien, et à la touche Échap
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

  /* ---------- Bouton retour en haut ------------------------------------- */
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

  /* ---------- Apparition au défilement (remplace AOS) --------------------
     Remplace la bibliothèque AOS, qui posait un problème sérieux : sa
     feuille de style met `[data-aos] { opacity: 0 }` en attendant que
     `AOS.init()` soit appelé. Si l'appel manque — ou échoue parce que le CDN
     ne répond pas — la section reste invisible sans le moindre message
     d'erreur. Ici, l'état par défaut est visible : en cas de panne du
     JavaScript, le contenu s'affiche quand même.                          */
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

  // Appelé par les pages qui insèrent du contenu après le démarrage.
  window.FLReveal = initReveal;

  /* ---------- Socle canvas ----------------------------------------------
     Un seul moteur pour toutes les visualisations :
     - redimensionne uniquement quand la taille change (au lieu de chaque image)
     - gère les écrans haute densité
     - met l'animation en pause hors écran et en onglet inactif (batterie)
     - se désactive si l'utilisateur demande moins d'animations
     ---------------------------------------------------------------------- */
  function createScene(canvas, drawFrame, opts) {
    if (!canvas || !canvas.getContext) return null;
    opts = opts || {};

    var ctx = canvas.getContext('2d', { alpha: false });
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = 0, h = 0, frame = 0, running = false, rafId = null, visible = false;

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

    function loop() {
      if (!running) return;
      if (fit()) drawFrame(ctx, w, h, frame++);
      rafId = requestAnimationFrame(loop);
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
      // Image fixe représentative : le contenu reste lisible, sans mouvement.
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

  // Exposé pour les pages qui ont leurs propres visualisations.
  window.FLScene = createScene;

  /* ---------- Oscilloscope du hero --------------------------------------
     Séquence : acquisition bruitée → filtrage → détection.
     Un seul moment orchestré, il boucle lentement.                        */
  function initHeroScope() {
    var canvas = $('#heroScope');
    if (!canvas) return;

    var elState = $('#scopeState'), elSnr = $('#scopeSnr'),
        elLat   = $('#scopeLat'),   elDec = $('#scopeDec');

    var BUF = 340, buf = [], t = 0, lastLabel = '';
    var PHASES = [
      { name: 'acquisition', until: 240, snr: '4.2 dB',  lat: '—',     dec: 'en attente' },
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

      buf.push(sample(t, phase));
      if (buf.length > BUF) buf.shift();
      t += 0.6;

      ctx.fillStyle = '#071620';
      ctx.fillRect(0, 0, w, h);

      // Réticule
      ctx.strokeStyle = 'rgba(31,154,168,0.10)';
      ctx.lineWidth = 1;
      for (var x = 0; x <= w; x += 44) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
      for (var y = 0; y <= h; y += 34) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }

      var isDetect = phase.name === 'détection';
      var color = isDetect ? '#c4703a' : '#2fb6c4';

      if (isDetect) {
        ctx.fillStyle = 'rgba(196,112,58,' + (0.06 + 0.05 * Math.sin(f * 0.25)) + ')';
        ctx.fillRect(0, 0, w, h);
      }

      var mid = h / 2, amp = h * 0.3;
      ctx.beginPath();
      for (var i = 0; i < buf.length; i++) {
        var px = (i / BUF) * w, py = mid - buf[i] * amp;
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.7;
      ctx.shadowColor = color;
      ctx.shadowBlur = isDetect ? 12 : 6;
      ctx.stroke();
      ctx.shadowBlur = 0;

      if (isDetect) {
        ctx.fillStyle = color;
        ctx.font = '500 12px "IBM Plex Mono", monospace';
        ctx.fillText('crise détectée', 12, 22);
      }
    }, { stillFrame: 300 });
  }

  /* ---------- Vignettes des fiches projet -------------------------------- */
  function initProjectViz() {
    // Vibration : signal sain puis impulsions périodiques de défaut
    var vib = $('#viz-vib');
    if (vib) {
      var vbuf = [], VB = 260, vt = 0;
      createScene(vib, function (ctx, w, h, f) {
        var fault = (f % 220) > 110;
        vt++;
        var s = Math.sin(vt * 0.12) * 0.2 + Math.sin(vt * 0.34) * 0.1 + (Math.random() - 0.5) * 0.05;
        if (fault) s += Math.exp(-Math.pow(vt % 18, 2) / 4) * 0.85 + Math.sin(vt * 1.1) * 0.25;
        vbuf.push(s);
        if (vbuf.length > VB) vbuf.shift();

        ctx.fillStyle = '#0b1a26'; ctx.fillRect(0, 0, w, h);
        var c = fault ? '#c4703a' : '#2fb6c4';
        ctx.beginPath();
        for (var i = 0; i < vbuf.length; i++) {
          var x = (i / VB) * w, y = h * 0.55 - vbuf[i] * h * 0.3;
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.strokeStyle = c; ctx.lineWidth = 1.5; ctx.stroke();
        ctx.fillStyle = c;
        ctx.font = '500 11px "IBM Plex Mono", monospace';
        ctx.fillText(fault ? 'défaut BPFI' : 'roulement sain', 12, 20);
      }, { stillFrame: 150 });
    }

    // Vision : cadres de détection qui se déplacent (sans getImageData, coûteux)
    var vis = $('#viz-vision');
    if (vis) {
      var objs = [
        { l: 'personne', c: '#2fb6c4', x: 0.14, y: 0.20, w: 0.20, h: 0.56, d: 0.0016 },
        { l: 'vélo',     c: '#c4703a', x: 0.58, y: 0.34, w: 0.28, h: 0.36, d: -0.0011 }
      ];
      createScene(vis, function (ctx, w, h, f) {
        ctx.fillStyle = '#0b1a26'; ctx.fillRect(0, 0, w, h);

        ctx.strokeStyle = 'rgba(255,255,255,0.05)'; ctx.lineWidth = 1;
        for (var y = 0; y <= h; y += 6) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }

        var scanY = (f * 1.6) % h;
        var g = ctx.createLinearGradient(0, scanY - 14, 0, scanY);
        g.addColorStop(0, 'rgba(47,182,196,0)');
        g.addColorStop(1, 'rgba(47,182,196,0.16)');
        ctx.fillStyle = g; ctx.fillRect(0, scanY - 14, w, 14);

        objs.forEach(function (o) {
          o.x += o.d;
          if (o.x < 0.02 || o.x + o.w > 0.98) o.d *= -1;
          var bx = o.x * w, by = o.y * h, bw = o.w * w, bh = o.h * h, cs = 11;
          ctx.strokeStyle = o.c; ctx.lineWidth = 2;
          [[bx, by, 1, 1], [bx + bw, by, -1, 1], [bx, by + bh, 1, -1], [bx + bw, by + bh, -1, -1]]
            .forEach(function (p) {
              ctx.beginPath();
              ctx.moveTo(p[0], p[1] + p[3] * cs);
              ctx.lineTo(p[0], p[1]);
              ctx.lineTo(p[0] + p[2] * cs, p[1]);
              ctx.stroke();
            });
          ctx.fillStyle = o.c;
          ctx.font = '500 11px "IBM Plex Mono", monospace';
          ctx.fillText(o.l, bx + 2, by - 6);
        });
      }, { stillFrame: 60 });
    }

    // EEG (vignette) : même logique que le hero, en plus sobre
    var eeg = $('#viz-eeg');
    if (eeg) {
      var ebuf = [], EB = 240, et = 0;
      createScene(eeg, function (ctx, w, h, f) {
        var crise = (f % 260) > 190;
        et += 0.7;
        var v = crise
          ? Math.sin(et * 0.5) * 0.3 + Math.sin(et * 1.8) * 0.55 + (Math.random() - 0.5) * 0.2
          : Math.sin(et * 0.08) * 0.34 + Math.sin(et * 0.22) * 0.13 + (Math.random() - 0.5) * 0.05;
        ebuf.push(v);
        if (ebuf.length > EB) ebuf.shift();

        ctx.fillStyle = '#0b1a26'; ctx.fillRect(0, 0, w, h);
        var c = crise ? '#c4703a' : '#2fb6c4';
        ctx.beginPath();
        for (var i = 0; i < ebuf.length; i++) {
          var x = (i / EB) * w, y = h / 2 - ebuf[i] * h * 0.3;
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.strokeStyle = c; ctx.lineWidth = 1.5; ctx.stroke();
        ctx.fillStyle = c;
        ctx.font = '500 11px "IBM Plex Mono", monospace';
        ctx.fillText(crise ? 'crise détectée' : 'EEG — Fp1', 12, 20);
      }, { stillFrame: 220 });
    }
  }

  /* ---------- Formulaire de contact -------------------------------------
     Envoi asynchrone : la personne reste sur la page et voit une confirmation.
     En cas d'échec, on donne une porte de sortie (l'adresse email).        */
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
      // Le formulaire reste fonctionnel sans JavaScript : on n'intercepte
      // que si l'action est bien configurée.
      var action = form.getAttribute('action') || '';
      if (action.indexOf('VOTRE_ID') !== -1 || !action) {
        e.preventDefault();
        say('Le formulaire n\'est pas encore relié à un service d\'envoi. Écrivez directement à lachanceawounang@icloud.com.', false);
        return;
      }

      e.preventDefault();
      if (form.querySelector('.hp') && form.querySelector('.hp').value) return; // piège à robots

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
          say('L\'envoi a échoué. Écrivez à lachanceawounang@icloud.com, la réponse sera la même.', false);
        })
        .then(function () {
          if (submit) { submit.disabled = false; submit.textContent = original; }
        });
    });
  }

  /* ---------- Démarrage -------------------------------------------------- */
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