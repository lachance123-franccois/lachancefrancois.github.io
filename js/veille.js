/* ==========================================================================
   veille.js — tableau de bord des offres collectées.

   Lit data/offers.json, produit par `python -m tracker.cli collect`.
   Aucune donnée d'exemple : si le fichier est absent ou vide, la page le dit
   et indique quoi lancer. La version précédente affichait des offres
   inventées chez Continental et au CNES.
   ========================================================================== */
(function () {
  'use strict';

  var LABELS = { internship: 'stages', phd: 'thèses', housing: 'logements' };

  var state = { kind: 'internship', query: '', data: null };
  var el = {};

  function $(id) { return document.getElementById(id); }

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function renderCounts(stats) {
    var byKind = (stats && stats.by_kind) || {};
    el.counts.innerHTML = ['internship', 'phd', 'housing'].map(function (k) {
      var total = (byKind[k] && byKind[k].total) || 0;
      return '<div><b class="metric">' + total + '</b><span>' + LABELS[k] + '</span></div>';
    }).join('');
  }

  function renderFreshness(generatedAt) {
    if (!generatedAt) {
      el.freshness.innerHTML =
        '<span class="pulse pulse--stale" aria-hidden="true"></span>' +
        'Date de collecte inconnue';
      return;
    }
    var when = new Date(generatedAt);
    var stale = (Date.now() - when.getTime()) / 3600000 > 36;
    el.freshness.innerHTML =
      '<span class="pulse' + (stale ? ' pulse--stale' : '') + '" aria-hidden="true"></span>' +
      'Dernière collecte : ' + when.toLocaleString('fr-FR') +
      (stale ? ' — la collecte ne tourne plus depuis plus de 36 h' : '');
  }

  function matches(offer, query) {
    if (!query) return true;
    var haystack = [
      offer.title, offer.organisation, offer.location,
      offer.source, (offer.keywords || []).join(' ')
    ].join(' ').toLowerCase();
    return query.toLowerCase().split(/\s+/).every(function (word) {
      return haystack.indexOf(word) !== -1;
    });
  }

  function offerHtml(offer) {
    var meta = [
      esc(offer.organisation),
      esc(offer.location),
      offer.price != null ? Math.round(offer.price) + ' €' : '',
      esc(offer.source)
    ].filter(Boolean).join(' · ');

    var keywords = (offer.keywords || []).slice(0, 6).map(function (k) {
      return '<li>' + esc(k) + '</li>';
    }).join('');

    return '<li class="board__item">' +
      '<h3><a href="' + esc(offer.url) + '" target="_blank" rel="noopener">' +
        esc(offer.title) + '</a></h3>' +
      (meta ? '<p class="board__meta">' + meta + '</p>' : '') +
      (offer.description
        ? '<p class="board__desc">' + esc(offer.description.slice(0, 240)) + '</p>' : '') +
      (keywords ? '<ul class="tags">' + keywords + '</ul>' : '') +
      '</li>';
  }

  function emptyState(reason) {
    var messages = {
      nofile: ['Aucune donnée disponible',
        'Deux causes possibles. Soit le fichier <code>data/offers.json</code> ' +
        "n'existe pas encore — le produire avec <code>python -m tracker.cli collect</code>. " +
        'Soit la page est ouverte directement depuis le disque ' +
        '(<code>file://</code>), où le navigateur interdit la lecture de ' +
        'fichiers locaux : lancer <code>python -m http.server 8000</code> ' +
        'dans le dossier du site, puis ouvrir <code>http://localhost:8000</code>.'],
      nooffers: ['Aucune offre dans cette catégorie',
        'Vérifier l\'état des sources avec <code>python -m tracker.cli check</code> : ' +
        'une source qui ne répond plus ressemble à une panne du programme.'],
      nomatch: ['Aucun résultat pour ce filtre',
        'Effacer le champ de recherche pour revoir toutes les offres.']
    };
    var m = messages[reason] || messages.nooffers;
    return '<li class="board__empty"><strong>' + m[0] + '</strong>' + m[1] + '</li>';
  }

  function setSearchEnabled(enabled, reason) {
    if (!el.search) return;
    el.search.disabled = !enabled;
    el.search.placeholder = enabled
      ? 'Filtrer par mot-clé, organisme ou lieu…'
      : reason;
    if (!enabled) el.search.value = '';
  }

  function render() {
    if (!state.data) {
      el.list.innerHTML = emptyState('nofile');
      el.count.textContent = '';
      setSearchEnabled(false, 'Rien à filtrer : aucune donnée chargée');
      return;
    }

    var offers = (state.data.offers && state.data.offers[state.kind]) || [];
    if (!offers.length) {
      el.list.innerHTML = emptyState('nooffers');
      el.count.textContent = '0 offre';
      setSearchEnabled(false, 'Rien à filtrer : aucune offre dans cette catégorie');
      return;
    }

    setSearchEnabled(true);

    var filtered = offers.filter(function (o) { return matches(o, state.query); });
    el.count.textContent = filtered.length + ' / ' + offers.length +
      ' offre' + (offers.length > 1 ? 's' : '');
    el.list.innerHTML = filtered.length
      ? filtered.map(offerHtml).join('')
      : emptyState('nomatch');
  }

  function init() {
    el.counts = $('boardCounts');
    el.freshness = $('boardFreshness');
    el.list = $('boardList');
    el.count = $('boardCount');
    el.tabs = $('boardTabs');
    el.search = $('boardSearch');
    if (!el.list) return;               // page sans tableau de bord

    el.tabs.addEventListener('click', function (e) {
      var button = e.target.closest('button[data-kind]');
      if (!button) return;
      state.kind = button.dataset.kind;
      Array.prototype.forEach.call(el.tabs.querySelectorAll('button'), function (b) {
        b.setAttribute('aria-selected', String(b === button));
      });
      render();
    });

    el.search.addEventListener('input', function (e) {
      state.query = e.target.value.trim();
      render();
    });

    fetch('data/offers.json', { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) {
        state.data = data;
        renderCounts(data.stats);
        renderFreshness(data.generated_at);
        render();
      })
      .catch(function () {
        renderCounts(null);
        renderFreshness(null);
        render();
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();