/* ==========================================================================
   projets-ml.js
   Remplace l'ancien système « panneau admin » : le code secret FL2025ML était
   écrit en clair dans le HTML, visible par n'importe quel visiteur, et les
   projets vivaient dans le localStorage — donc invisibles pour un recruteur
   sur son propre navigateur. Les projets sont maintenant dans le code source,
   versionnés avec le site.
   ========================================================================== */
(function () {
  'use strict';

  var GH = 'https://github.com/lachance123-franccois/';

  /* Chaque projet peut porter une clé `result` : une phrase courte avec un
     chiffre mesuré, affichée dans un encadré. Elle est volontairement absente
     tant que le chiffre n'a pas été relevé — une fiche sans résultat est
     neutre, une fiche avec un résultat indéfendable en entretien ne l'est pas.

     Pour en ajouter une :
         result: 'Exactitude 91 % sur les 1 200 images de test du jeu X.'
     La métrique, la valeur, et sur quoi elle a été mesurée. */
  var PROJECTS = [
    {
      title: 'Prévision de séries temporelles par LSTM',
      domain: 'Séries temporelles',
      desc: 'Modélisation de flux économiques par réseau récurrent : fenêtrage, normalisation, entraînement et comparaison à une référence naïve.',
      techs: ['TensorFlow', 'Python', 'LSTM'],
      link: GH + 'pipeline_serie-temporelle',
      icon: 'fa-chart-line', tone: 'signal'
    },
    {
      title: 'Classification de radiographies pulmonaires',
      domain: 'Imagerie médicale',
      desc: 'Classification d\'images médicales par réseau convolutif ResNet, avec augmentation de données et suivi du surapprentissage.',
      techs: ['PyTorch', 'ResNet', 'OpenCV'],
      link: GH + 'classification_trash',
      icon: 'fa-lungs', tone: 'detect'
    },
    {
      title: 'Analyse de sentiment par BERT',
      domain: 'Traitement du langage',
      desc: 'Affinage d\'un modèle BERT pour la classification multi-classe de textes, avec analyse des erreurs par classe.',
      techs: ['Hugging Face', 'BERT', 'Python'],
      link: GH + 'analyse_bert',
      icon: 'fa-language', tone: 'ink'
    },
    {
      title: 'Classification de graines par image',
      domain: 'Vision par ordinateur',
      desc: 'Reconnaissance de variétés de graines à partir de photographies : segmentation, descripteurs de forme et de texture, puis classification.',
      techs: ['scikit-learn', 'OpenCV', 'pandas'],
      link: GH + 'riceclassification2.0',
      icon: 'fa-seedling', tone: 'signal'
    },
    {
      title: 'Régression linéaire — de la théorie au code',
      domain: 'Fondamentaux',
      desc: 'Implémentation de la régression linéaire depuis les équations : moindres carrés, descente de gradient, régularisation, diagnostics de résidus.',
      techs: ['NumPy', 'Python', 'Statistiques'],
      link: GH + 'regression-lineaire',
      icon: 'fa-chart-simple', tone: 'ink'
    },
    {
      title: 'Prévision météorologique',
      domain: 'Séries temporelles',
      desc: 'Prédiction de variables climatiques par modèles ARIMA et Prophet, avec validation glissante dans le temps.',
      techs: ['Prophet', 'statsmodels', 'pandas'],
      link: GH + 'pipeline_serie-temporelle',
      icon: 'fa-cloud-sun', tone: 'detect'
    }
  ];

  // Trois tons tirés du design system. L'ancienne version tirait six
  // dégradés sans rapport les uns avec les autres (rose, orange, violet…),
  // ce qui donnait une page arlequin. Trois suffisent à distinguer les
  // familles de projets.
  var TONES = {
    signal: 'linear-gradient(135deg, #1f9aa8 0%, #16303f 100%)',
    detect: 'linear-gradient(135deg, #c4703a 0%, #16303f 100%)',
    ink:    'linear-gradient(135deg, #16303f 0%, #0b1a26 100%)'
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
          '<div class="project-card h-100 d-flex flex-column">' +
            '<div class="project-image-placeholder" style="background: ' +
                (TONES[p.tone] || TONES.ink) + ';" aria-hidden="true">' +
              '<i class="fas ' + escapeHtml(p.icon || 'fa-diagram-project') + ' fa-3x"></i>' +
              '<div class="project-overlay">' +
                '<a class="btn btn-light rounded-pill px-4" href="' + escapeHtml(p.link) +
                '" target="_blank" rel="noopener" tabindex="-1">Voir le code</a>' +
              '</div>' +
            '</div>' +
            '<div class="p-4 d-flex flex-column h-100">' +
              '<p class="entry__domain mb-1">' + escapeHtml(p.domain) + '</p>' +
              '<h3 class="h5 mt-1">' + escapeHtml(p.title) + '</h3>' +
              '<p class="text-muted small">' + escapeHtml(p.desc) + '</p>' +
              (p.result ? '<p class="entry__result small">' + escapeHtml(p.result) + '</p>' : '') +
              '<div class="mt-auto">' +
                '<div class="mb-3">' + tags + '</div>' +
                '<a class="entry__link" href="' + escapeHtml(p.link) + '" target="_blank" rel="noopener">Lire le code</a>' +
              '</div>' +
            '</div>' +
          '</div>' +
        '</div>';
    }).join('');

    // Les cartes viennent d'être insérées : main.js doit les observer.
    if (typeof window.FLReveal === 'function') window.FLReveal();
  }

  /* ---------- Vignettes animées des projets signal ----------------------- */
  function initCanvases() {
    var scene = window.FLScene;
    if (typeof scene !== 'function') return;

    // EEG — signal calme puis crise
    var eeg = document.getElementById('canvas-eeg');
    if (eeg) {
      var eb = [], EB = 260, et = 0;
      scene(eeg, function (ctx, w, h, f) {
        var crise = (f % 300) > 220;
        et += 0.7;
        var v = crise
          ? Math.sin(et * 0.5) * 0.3 + Math.sin(et * 1.8) * 0.55 + (Math.random() - 0.5) * 0.22
          : Math.sin(et * 0.08) * 0.34 + Math.sin(et * 0.22) * 0.13 + (Math.random() - 0.5) * 0.05;
        eb.push(v); if (eb.length > EB) eb.shift();

        ctx.fillStyle = '#0b1a26'; ctx.fillRect(0, 0, w, h);
        ctx.strokeStyle = 'rgba(47,182,196,0.08)'; ctx.lineWidth = 1;
        for (var x = 0; x <= w; x += 36) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }

        var c = crise ? '#c4703a' : '#2fb6c4';
        ctx.beginPath();
        for (var i = 0; i < eb.length; i++) {
          var px = (i / EB) * w, py = h / 2 - eb[i] * h * 0.3;
          i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.strokeStyle = c; ctx.lineWidth = 1.6; ctx.stroke();
        ctx.fillStyle = c; ctx.font = '500 11px "IBM Plex Mono", monospace';
        ctx.fillText(crise ? 'crise détectée' : 'EEG — canal Fp1', 12, 20);
      }, { stillFrame: 250 });
    }

    // Roulement — impulsions de défaut
    var rou = document.getElementById('canvas-roulement');
    if (rou) {
      var vb = [], VB = 260, vt = 0;
      scene(rou, function (ctx, w, h, f) {
        var fault = (f % 240) > 120;
        vt++;
        var s = Math.sin(vt * 0.12) * 0.2 + Math.sin(vt * 0.34) * 0.1 + (Math.random() - 0.5) * 0.05;
        if (fault) s += Math.exp(-Math.pow(vt % 18, 2) / 4) * 0.85 + Math.sin(vt * 1.1) * 0.25;
        vb.push(s); if (vb.length > VB) vb.shift();

        ctx.fillStyle = '#0b1a26'; ctx.fillRect(0, 0, w, h);
        var c = fault ? '#c4703a' : '#2fb6c4';
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

    // Constellation QAM-16 — le bruit monte puis redescend
    var qam = document.getElementById('canvas-qam');
    if (qam) {
      var ideal = [];
      [-3, -1, 1, 3].forEach(function (i) { [-3, -1, 1, 3].forEach(function (q) { ideal.push([i, q]); }); });
      var noise = 0.05, dir = 1;
      scene(qam, function (ctx, w, h) {
        noise += dir * 0.003;
        if (noise > 0.5 || noise < 0.04) dir *= -1;

        ctx.fillStyle = '#0b1a26'; ctx.fillRect(0, 0, w, h);
        var sc = Math.min(w, h) * 0.1, ox = w / 2, oy = h / 2;

        ctx.strokeStyle = 'rgba(47,182,196,0.14)'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(0, oy); ctx.lineTo(w, oy); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(ox, 0); ctx.lineTo(ox, h); ctx.stroke();

        var degrade = noise > 0.3;
        var col = degrade ? '#c4703a' : '#2fb6c4';
        ideal.forEach(function (p) {
          var rx = ox + (p[0] + (Math.random() - 0.5) * noise * 2) * sc;
          var ry = oy - (p[1] + (Math.random() - 0.5) * noise * 2) * sc;
          ctx.beginPath(); ctx.arc(rx, ry, 3, 0, Math.PI * 2);
          ctx.fillStyle = col; ctx.fill();
        });

        ctx.fillStyle = col; ctx.font = '500 11px "IBM Plex Mono", monospace';
        ctx.fillText('TEB ≈ ' + (noise * noise * 0.5).toFixed(4), 12, 20);
      }, { stillFrame: 40 });
    }

    // Vision — cadres de détection (sans getImageData, qui saturait le processeur)
    var vis = document.getElementById('canvas-vision');
    if (vis) {
      var objs = [
        { l: 'personne 0.94', c: '#2fb6c4', x: 0.14, y: 0.20, w: 0.20, h: 0.56, d: 0.0016 },
        { l: 'voiture 0.87',  c: '#c4703a', x: 0.56, y: 0.40, w: 0.30, h: 0.30, d: -0.0011 }
      ];
      scene(vis, function (ctx, w, h, f) {
        ctx.fillStyle = '#0b1a26'; ctx.fillRect(0, 0, w, h);
        ctx.strokeStyle = 'rgba(255,255,255,0.04)'; ctx.lineWidth = 1;
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