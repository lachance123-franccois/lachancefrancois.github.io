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

    // Test d'intervention do(biais) : radiographie à gauche, jauge de
    // probabilité à droite. Le glyphe apparaît, l'attention Grad-CAM quitte
    // les poumons pour le coin, la probabilité bascule — et pas un pixel du
    // parenchyme n'a changé. C'est le mécanisme que le projet mesure.
    var scc = document.getElementById('canvas-shortcut');
    if (scc) {
      var elState = document.getElementById('scState');
      var elProb  = document.getElementById('scProb');
      var elFocus = document.getElementById('scFocus');
      var lastState = '';

      scene(scc, function (ctx, w, h, f) {
        var cycle = f % 400;
        var g = cycle < 110 ? 0
              : cycle < 190 ? (cycle - 110) / 80
              : cycle < 310 ? 1
              : 1 - (cycle - 310) / 80;
        g = Math.max(0, Math.min(1, g));

        // Valeurs mesurées dans le projet : ATE = +0.466
        var prob = 0.19 + 0.466 * g;
        var focus = 0.31 + (1.87 - 0.31) * g;
        var state = g > 0.5 ? 'biais = 1' : 'biais = 0';
        if (state !== lastState) { lastState = state; if (elState) elState.textContent = state; }
        if (elProb)  elProb.textContent  = prob.toFixed(2);
        if (elFocus) elFocus.textContent = '×' + focus.toFixed(2);

        ctx.fillStyle = '#071620';
        ctx.fillRect(0, 0, w, h);

        var imgW = Math.min(w * 0.52, h * 1.05);
        var ox = 18, oy = (h - imgW * 0.92) / 2, side = imgW * 0.92;
        var cx = ox + side / 2, cy = oy + side * 0.54, r = side * 0.34;

        // Thorax
        ctx.save(); ctx.translate(cx, cy); ctx.scale(0.86, 1);
        ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(190,205,212,0.3)'; ctx.fill();
        ctx.restore();

        // Champs pulmonaires : rigoureusement identiques tout au long
        [-1, 1].forEach(function (sd) {
          ctx.save();
          ctx.translate(cx + sd * r * 0.38, cy - r * 0.06);
          ctx.scale(0.42, 0.78);
          ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2);
          ctx.fillStyle = '#0d2230'; ctx.fill();
          ctx.restore();
        });
        ctx.fillStyle = 'rgba(210,222,228,0.38)';
        ctx.fillRect(cx - 1.5, cy - r * 0.85, 3, r * 1.7);

        // Chaleur Grad-CAM : sur les poumons quand g=0, sur le coin quand g=1
        function heat(hx, hy, rad, intensity) {
          if (intensity < 0.02) return;
          var grd = ctx.createRadialGradient(hx, hy, 0, hx, hy, rad);
          grd.addColorStop(0, 'rgba(196,112,58,' + (0.5 * intensity) + ')');
          grd.addColorStop(0.5, 'rgba(196,112,58,' + (0.2 * intensity) + ')');
          grd.addColorStop(1, 'rgba(196,112,58,0)');
          ctx.fillStyle = grd;
          ctx.beginPath(); ctx.arc(hx, hy, rad, 0, Math.PI * 2); ctx.fill();
        }
        heat(cx - r * 0.38, cy - r * 0.06, r * 0.55, 1 - g);
        heat(cx + r * 0.38, cy - r * 0.06, r * 0.55, 1 - g);
        heat(ox + side * 0.11, oy + side * 0.11, r * 0.5, g);

        // Le glyphe
        if (g > 0.01) {
          var gx = ox + side * 0.05, gy = oy + side * 0.05, gs = side * 0.13;
          ctx.strokeStyle = 'rgba(255,255,255,' + (0.9 * g) + ')';
          ctx.lineWidth = 3;
          ctx.beginPath();
          ctx.moveTo(gx, gy); ctx.lineTo(gx, gy + gs); ctx.lineTo(gx + gs * 0.7, gy + gs);
          ctx.stroke();
        }

        // Cadre de l'image
        ctx.strokeStyle = 'rgba(255,255,255,0.12)';
        ctx.lineWidth = 1;
        ctx.strokeRect(ox, oy, side, side * 0.92);

        // Jauge de probabilité à droite
        var bx = ox + side + 34, bw = Math.max(w - bx - 26, 40);
        var by = oy + side * 0.30, bh = 18;

        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        ctx.font = '400 10.5px "IBM Plex Mono", monospace';
        ctx.fillText('P(malade)', bx, by - 10);

        ctx.fillStyle = 'rgba(255,255,255,0.08)';
        ctx.fillRect(bx, by, bw, bh);
        ctx.fillStyle = prob > 0.5 ? '#c4703a' : '#2fb6c4';
        ctx.fillRect(bx, by, bw * prob, bh);

        // Seuil de décision
        ctx.strokeStyle = 'rgba(255,255,255,0.55)';
        ctx.setLineDash([3, 3]); ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(bx + bw * 0.5, by - 5); ctx.lineTo(bx + bw * 0.5, by + bh + 5);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(255,255,255,0.4)';
        ctx.font = '400 9px "IBM Plex Mono", monospace';
        ctx.fillText('seuil 0.50', bx + bw * 0.5 - 24, by + bh + 18);

        // Verdict
        ctx.fillStyle = prob > 0.5 ? '#c4703a' : '#2fb6c4';
        ctx.font = '500 15px "IBM Plex Mono", monospace';
        ctx.fillText(prob > 0.5 ? 'malade' : 'sain', bx, by + bh + 46);

        ctx.fillStyle = 'rgba(255,255,255,0.35)';
        ctx.font = '400 10px "IBM Plex Mono", monospace';
        ctx.fillText('parenchyme identique', bx, by + bh + 68);
      }, { stillFrame: 250 });
    }

    // Diagramme de fiabilité : les barres d'exactitude, d'abord sous la
    // diagonale parce que le modèle annonce plus de certitude qu'il n'en
    // mérite, remontent vers elle après recalibration. C'est exactement ce
    // que mesure l'ECE.
    var uq = document.getElementById('canvas-uq');
    if (uq) {
      var label = document.getElementById('uqState');
      var BINS = 10;
      // Écart initial par tranche de confiance : plus le modèle est sûr,
      // plus il se surestime.
      var GAP = [0.02, 0.03, 0.05, 0.08, 0.11, 0.15, 0.19, 0.23, 0.26, 0.28];
      var MASS = [0.01, 0.01, 0.02, 0.03, 0.04, 0.06, 0.09, 0.14, 0.26, 0.34];
      var last = '';

      scene(uq, function (ctx, w, h, f) {
        var cycle = f % 420;
        // 0 → 1 : proportion de l'écart déjà corrigé
        var fix = cycle < 140 ? 0
                : cycle < 240 ? (cycle - 140) / 100
                : cycle < 340 ? 1
                : 1 - (cycle - 340) / 80;
        fix = Math.max(0, Math.min(1, fix));

        var state = fix < 0.15 ? 'modèle brut'
                  : fix > 0.85 ? 'après recalibration' : 'recalibration…';
        if (label && state !== last) { label.textContent = state; last = state; }

        ctx.fillStyle = '#071620';
        ctx.fillRect(0, 0, w, h);

        var pad = 40, x0 = pad, y0 = h - 34, x1 = w - 16, y1 = 14;
        var pw = x1 - x0, ph = y0 - y1;

        // Grille
        ctx.strokeStyle = 'rgba(47,182,196,0.10)';
        ctx.lineWidth = 1;
        for (var g = 0; g <= 5; g++) {
          var gx = x0 + (pw * g) / 5, gy = y0 - (ph * g) / 5;
          ctx.beginPath(); ctx.moveTo(gx, y1); ctx.lineTo(gx, y0); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(x0, gy); ctx.lineTo(x1, gy); ctx.stroke();
        }

        // Barres : exactitude réelle par tranche de confiance
        var bw = pw / BINS;
        for (var i = 0; i < BINS; i++) {
          var conf = (i + 0.5) / BINS;
          var acc = Math.max(0, conf - GAP[i] * (1 - fix));
          var bx = x0 + i * bw;

          // Écart restant, en ambre
          if (acc < conf - 0.002) {
            ctx.fillStyle = 'rgba(196,112,58,0.35)';
            ctx.fillRect(bx + 2, y0 - conf * ph, bw - 4, (conf - acc) * ph);
          }
          // Exactitude mesurée
          ctx.fillStyle = 'rgba(47,182,196,' + (0.35 + 0.45 * MASS[i] / 0.34) + ')';
          ctx.fillRect(bx + 2, y0 - acc * ph, bw - 4, acc * ph);
        }

        // Diagonale : calibration parfaite
        ctx.strokeStyle = 'rgba(255,255,255,0.55)';
        ctx.setLineDash([4, 4]);
        ctx.lineWidth = 1.2;
        ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
        ctx.setLineDash([]);

        // Axes
        ctx.strokeStyle = 'rgba(255,255,255,0.25)';
        ctx.beginPath();
        ctx.moveTo(x0, y1); ctx.lineTo(x0, y0); ctx.lineTo(x1, y0);
        ctx.stroke();

        // Graduations : sans elles, le lecteur ne sait pas que les deux axes
        // vont de 0 à 1 et la diagonale ne veut plus rien dire.
        ctx.fillStyle = 'rgba(255,255,255,0.45)';
        ctx.font = '400 9px "IBM Plex Mono", monospace';
        ['0', '0.5', '1'].forEach(function (t, i) {
          ctx.textAlign = 'center';
          ctx.fillText(t, x0 + (pw * i) / 2, y0 + 12);
          ctx.textAlign = 'right';
          ctx.fillText(t, x0 - 5, y0 - (ph * i) / 2 + 3);
        });
        ctx.textAlign = 'left';

        // Nom des axes
        ctx.fillStyle = 'rgba(255,255,255,0.55)';
        ctx.font = '400 9.5px "IBM Plex Mono", monospace';
        ctx.textAlign = 'center';
        ctx.fillText('confiance annoncée', x0 + pw / 2, y0 + 23);
        ctx.save();
        ctx.translate(11, y1 + ph / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('exactitude réelle', 0, 0);
        ctx.restore();
        ctx.textAlign = 'left';

        // Étiquette de la diagonale
        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        ctx.font = '400 9px "IBM Plex Mono", monospace';
        ctx.save();
        ctx.translate(x1 - 92, y1 + 26);
        ctx.rotate(-Math.atan2(ph, pw));
        ctx.fillText('calibration parfaite', 0, 0);
        ctx.restore();

        // Légende de l'écart, tant qu'il est visible
        if (fix < 0.9) {
          ctx.fillStyle = 'rgba(196,112,58,' + (0.35 * (1 - fix) + 0.25) + ')';
          ctx.fillRect(x0 + 10, y1 + 28, 9, 9);
          ctx.fillStyle = 'rgba(255,255,255,' + (0.5 * (1 - fix) + 0.2) + ')';
          ctx.font = '400 9.5px "IBM Plex Mono", monospace';
          ctx.fillText('excès de confiance', x0 + 24, y1 + 36);
        }

        // ECE courant, calculé sur les mêmes chiffres que les barres
        var ece = 0;
        for (var j = 0; j < BINS; j++) ece += MASS[j] * GAP[j] * (1 - fix);
        ctx.fillStyle = fix > 0.85 ? '#2fb6c4' : '#c4703a';
        ctx.font = '500 12px "IBM Plex Mono", monospace';
        ctx.fillText('ECE ' + ece.toFixed(3), x0 + 10, y1 + 18);
      }, { stillFrame: 300 });
    }

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