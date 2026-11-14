(function () {
  'use strict';

  var GH = 'https://github.com/lachance123-franccois/';

  var PROJECTS = [
    {
      title: 'Prévision de séries temporelles par LSTM',
      domain: 'Séries temporelles',
      desc: 'Modélisation de flux économiques par réseau récurrent : fenêtrage, normalisation, entraînement et comparaison à une référence naïve.',
      techs: ['TensorFlow', 'LSTM', 'Fenêtrage'],
      link: GH + 'pipeline_serie-temporelle'
    },
    {
      title: 'Classification de radiographies pulmonaires',
      domain: 'Imagerie médicale',
      desc: 'Classification d\'images médicales par réseau convolutif ResNet, avec augmentation de données et suivi du surapprentissage.',
      techs: ['PyTorch', 'ResNet', 'OpenCV'],
      link: GH + 'classification_trash'   /* À VÉRIFIER : le nom du dépôt ne correspond pas au projet */
    },
    {
      title: 'Analyse de sentiment par BERT',
      domain: 'Traitement du langage',
      desc: 'Affinage d\'un modèle BERT pour la classification multi-classe de textes, avec analyse des erreurs par classe.',
      techs: ['Hugging Face', 'BERT', 'Multi-classe'],
      link: GH + 'analyse_bert'
    },
    {
      title: 'Classification de graines par image',
      domain: 'Vision par ordinateur',
      desc: 'Reconnaissance de variétés de graines à partir de photographies : segmentation, descripteurs de forme et de texture, puis classification.',
      techs: ['scikit-learn', 'OpenCV', 'pandas'],
      link: GH + 'riceclassification2.0'
    },
    {
      title: 'Régression linéaire : de la théorie au code',
      domain: 'Fondamentaux',
      desc: 'Implémentation de la régression linéaire depuis les équations : moindres carrés, descente de gradient, régularisation, diagnostics de résidus.',
      techs: ['NumPy', 'Moindres carrés', 'Statistiques'],
      link: GH + 'regression-lineaire'
    },
    {
      title: 'Prévision météorologique',
      domain: 'Séries temporelles',
      desc: 'Prédiction de variables climatiques par modèles ARIMA et Prophet, avec validation glissante dans le temps.',
      techs: ['Prophet', 'statsmodels', 'pandas'],
      link: GH + 'pipeline_serie-temporelle'   /* À VÉRIFIER : même dépôt que le projet LSTM */
    }
  ];

  /* Couleurs et cadence partagées avec js/main.js (repli si main.js est absent) */
  var V = window.FLViz || {};
  var STEP = V.STEP || 1;
  var C = V.C || {
    vizBg: '#eaf2fa', line: '#0e7490', alert: '#b45309',
    scopeBg: '#071a33', glow: '#06b6d4', glowWarn: '#f59e0b'
  };

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function render() {
    var container = document.getElementById('projectsContainer');
    if (!container) return;

    container.innerHTML = PROJECTS.map(function (p) {
      var tags = p.techs.map(function (t) {
        return '<span class="tech-badge">' + escapeHtml(t) + '</span>';
      }).join('');

      return '' +
        '<div class="col-md-6 col-lg-4 reveal">' +
          '<article class="project-card">' +
            '<div class="p-4">' +
              '<p class="card__domain">' + escapeHtml(p.domain) + '</p>' +
              '<h3>' + escapeHtml(p.title) + '</h3>' +
              '<p class="text-muted">' + escapeHtml(p.desc) + '</p>' +
              '<div class="card__foot">' +
                tags +
                '<div class="card__links"><a href="' + escapeHtml(p.link) +
                '" target="_blank" rel="noopener">Voir le projet sur GitHub →</a></div>' +
              '</div>' +
            '</div>' +
          '</article>' +
        '</div>';
    }).join('');

    if (typeof window.FLReveal === 'function') window.FLReveal();
  }

  function initCanvases() {
    var scene = window.FLScene;
    if (typeof scene !== 'function') return;

    var eeg = document.getElementById('canvas-eeg');
    if (eeg) {
      var eb = [], EB = 260, et = 0;
      scene(eeg, function (ctx, w, h, f) {
        var crise = (f % 300) > 220;
        for (var k = 0; k < STEP; k++) {
          et += 0.7;
          var v = crise
            ? Math.sin(et * 0.5) * 0.3 + Math.sin(et * 1.8) * 0.55 + (Math.random() - 0.5) * 0.22
            : Math.sin(et * 0.08) * 0.34 + Math.sin(et * 0.22) * 0.13 + (Math.random() - 0.5) * 0.05;
          eb.push(v); if (eb.length > EB) eb.shift();
        }

        ctx.fillStyle = C.vizBg; ctx.fillRect(0, 0, w, h);
        ctx.strokeStyle = 'rgba(14,116,144,0.08)'; ctx.lineWidth = 1;
        for (var x = 0; x <= w; x += 36) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }

        var c = crise ? C.alert : C.line;
        ctx.beginPath();
        for (var i = 0; i < eb.length; i++) {
          var px = (i / EB) * w, py = h / 2 - eb[i] * h * 0.3;
          i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.strokeStyle = c; ctx.lineWidth = 1.6; ctx.stroke();
        ctx.fillStyle = c; ctx.font = '500 11px "IBM Plex Mono", monospace';
        ctx.fillText(crise ? 'crise détectée' : 'EEG · canal Fp1', 12, 20);
      }, { stillFrame: 250 });
    }

    var rou = document.getElementById('canvas-roulement');
    if (rou) {
      var vb = [], VB = 260, vt = 0;
      scene(rou, function (ctx, w, h, f) {
        var fault = (f % 240) > 120;
        for (var k = 0; k < STEP; k++) {
          vt++;
          var s = Math.sin(vt * 0.12) * 0.2 + Math.sin(vt * 0.34) * 0.1 + (Math.random() - 0.5) * 0.05;
          if (fault) s += Math.exp(-Math.pow(vt % 18, 2) / 4) * 0.85 + Math.sin(vt * 1.1) * 0.25;
          vb.push(s); if (vb.length > VB) vb.shift();
        }

        ctx.fillStyle = C.vizBg; ctx.fillRect(0, 0, w, h);
        var c = fault ? C.alert : C.line;
        ctx.beginPath();
        for (var i = 0; i < vb.length; i++) {
          var x = (i / VB) * w, y = h * 0.55 - vb[i] * h * 0.3;
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.strokeStyle = c; ctx.lineWidth = 1.6; ctx.stroke();
        ctx.fillStyle = c; ctx.font = '500 11px "IBM Plex Mono", monospace';
        ctx.fillText(fault ? 'défaut BPFI' : 'roulement sain', 12, 20);
      }, { stillFrame: 180 });
    }

    var qam = document.getElementById('canvas-qam');
    if (qam) {
      var ideal = [];
      [-3, -1, 1, 3].forEach(function (i) { [-3, -1, 1, 3].forEach(function (q) { ideal.push([i, q]); }); });
      var noise = 0.05, dir = 1;
      scene(qam, function (ctx, w, h) {
        noise += dir * 0.003 * STEP;
        if (noise > 0.5 || noise < 0.04) dir *= -1;

        ctx.fillStyle = C.vizBg; ctx.fillRect(0, 0, w, h);
        var sc = Math.min(w, h) * 0.1, ox = w / 2, oy = h / 2;

        ctx.strokeStyle = 'rgba(14,116,144,0.20)'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(0, oy); ctx.lineTo(w, oy); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(ox, 0); ctx.lineTo(ox, h); ctx.stroke();

        var degrade = noise > 0.3;
        var col = degrade ? C.alert : C.line;
        ideal.forEach(function (p) {
          var rx = ox + (p[0] + (Math.random() - 0.5) * noise * 2) * sc;
          var ry = oy - (p[1] + (Math.random() - 0.5) * noise * 2) * sc;
          ctx.beginPath(); ctx.arc(rx, ry, 3, 0, Math.PI * 2);
          ctx.fillStyle = col; ctx.fill();
        });

        ctx.fillStyle = col; ctx.font = '500 11px "IBM Plex Mono", monospace';
        ctx.fillText(degrade ? 'canal bruité' : 'constellation QAM-16', 12, 20);
      }, { stillFrame: 40 });
    }

    var vis = document.getElementById('canvas-vision');
    if (vis) {
      var objs = [
        { l: 'personne', c: C.line, x: 0.14, y: 0.20, w: 0.20, h: 0.56, d: 0.0016 },
        { l: 'voiture',  c: C.alert, x: 0.56, y: 0.40, w: 0.30, h: 0.30, d: -0.0011 }
      ];
      scene(vis, function (ctx, w, h, f) {
        ctx.fillStyle = C.vizBg; ctx.fillRect(0, 0, w, h);
        ctx.strokeStyle = 'rgba(15,33,55,0.05)'; ctx.lineWidth = 1;
        for (var y = 0; y <= h; y += 6) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }

        var scanY = (f * 1.6) % h;
        var g = ctx.createLinearGradient(0, scanY - 14, 0, scanY);
        g.addColorStop(0, 'rgba(14,116,144,0)');
        g.addColorStop(1, 'rgba(14,116,144,0.14)');
        ctx.fillStyle = g; ctx.fillRect(0, scanY - 14, w, 14);

        objs.forEach(function (o) {
          o.x += o.d * STEP;
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
          ctx.fillStyle = o.c; ctx.font = '500 11px "IBM Plex Mono", monospace';
          ctx.fillText(o.l, bx + 2, by - 6);
        });
      }, { stillFrame: 60 });
    }
  }

  function boot() { render(); initCanvases(); }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();