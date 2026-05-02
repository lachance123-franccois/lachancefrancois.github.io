// ===========================
// CONFIGURATION
// ===========================
const CONFIG = {
    STORAGE_KEYS: {
        SEARCHES: 'linkedin_searches',
        FAVORITES: 'linkedin_favorites',
        HISTORY: 'linkedin_history',
        THEME: 'linkedin_theme',
        STATS: 'linkedin_stats'
    },
    MAX_HISTORY: 50,
    MAX_FAVORITES: 20
};

// ===========================
// STATE MANAGEMENT
// ===========================
let state = {
    currentResults: [],
    searchHistory: [],
    favorites: [],
    stats: {
        totalSearches: 0,
        linksGenerated: 0,
        savedSearches: 0
    }
};

// ===========================
// INITIALIZATION
// ===========================
document.addEventListener('DOMContentLoaded', function() {
    console.log('🐵 LinkedIn Stage Tracker initialized');
    loadFromStorage();
    updateStats();
    renderHistory();
    renderFavorites();
    initializeTheme();
});

// ===========================
// THEME MANAGEMENT
// ===========================
function initializeTheme() {
    const savedTheme = localStorage.getItem(CONFIG.STORAGE_KEYS.THEME) || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem(CONFIG.STORAGE_KEYS.THEME, newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('.theme-icon');
    icon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// ===========================
// STORAGE FUNCTIONS
// ===========================
function loadFromStorage() {
    try {
        state.searchHistory = JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.HISTORY) || '[]');
        state.favorites = JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.FAVORITES) || '[]');
        state.stats = JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.STATS) || JSON.stringify(state.stats));
    } catch (error) {
        console.error('Error loading from storage:', error);
    }
}

function saveToStorage() {
    try {
        localStorage.setItem(CONFIG.STORAGE_KEYS.HISTORY, JSON.stringify(state.searchHistory));
        localStorage.setItem(CONFIG.STORAGE_KEYS.FAVORITES, JSON.stringify(state.favorites));
        localStorage.setItem(CONFIG.STORAGE_KEYS.STATS, JSON.stringify(state.stats));
    } catch (error) {
        console.error('Error saving to storage:', error);
    }
}

// ===========================
// SEARCH LINK GENERATION
// ===========================
function generateSearchLinks() {
    const keywords = document.getElementById('keywords').value.trim();
    const location = document.getElementById('location').value.trim();
    const experience = document.getElementById('experience').value;
    const datePosted = document.getElementById('datePosted').value;

    if (!keywords) {
        showAlert('Veuillez entrer au moins un mot-clé !', 'warning');
        return;
    }

    // Show loading
    showLoading(true);
    hideElement('results');
    
    // Simulate processing delay for better UX
    setTimeout(() => {
        const searches = generateMultipleSearches(keywords, location, experience, datePosted);
        
        // Save to history
        addToHistory({
            keywords,
            location,
            experience,
            datePosted,
            timestamp: new Date().toISOString(),
            id: generateId()
        });

        // Update stats
        state.stats.totalSearches++;
        state.stats.linksGenerated += searches.length;
        
        // Store current results
        state.currentResults = searches;
        
        // Display results
        displaySearchResults(searches);
        
        // Update UI
        showLoading(false);
        updateStats();
        showTabs();
        showTab('results');
        
        saveToStorage();

        // Success message
        showAlert(`✅ ${searches.length} liens de recherche générés avec succès !`, 'success');
    }, 1000);
}

function generateMultipleSearches(keywords, location, experience, datePosted) {
    const searches = [];
    
    const searchTypes = [
        { prefix: 'stage', type: 'primary', icon: '🎓' },
        { prefix: 'internship', type: 'alternative', icon: '💼' },
        { prefix: 'alternance', type: 'alternative', icon: '🔄' },
        { prefix: 'étudiant', type: 'student', icon: '📚' }
    ];

    searchTypes.forEach(searchType => {
        const fullKeywords = `${searchType.prefix} ${keywords}`;
        searches.push({
            id: generateId(),
            title: `${searchType.icon} ${capitalizeFirst(searchType.prefix)} - ${keywords}`,
            url: buildLinkedInUrl(fullKeywords, location, experience, datePosted),
            type: searchType.type,
            keywords: fullKeywords,
            location,
            experience,
            datePosted,
            timestamp: new Date().toISOString()
        });
    });

    return searches;
}

function buildLinkedInUrl(keywords, location, experience, datePosted) {
    let url = 'https://www.linkedin.com/jobs/search/?';
    const params = [];
    
    if (keywords) params.push('keywords=' + encodeURIComponent(keywords));
    if (location) params.push('location=' + encodeURIComponent(location));
    if (experience) params.push('f_E=' + experience);
    if (datePosted) params.push('f_TPR=' + datePosted);
    
    // Add internship filter
    params.push('f_JT=I');
    
    url += params.join('&');
    return url;
}

// ===========================
// DISPLAY FUNCTIONS
// ===========================
function displaySearchResults(searches) {
    const resultsDiv = document.getElementById('results');
    
    if (searches.length === 0) {
        resultsDiv.innerHTML = getEmptyState('🔍', 'Aucun résultat', 'Effectuez une recherche pour voir les résultats ici');
        return;
    }

    let html = '';
    
    searches.forEach((search, index) => {
        html += `
            <div class="search-card" style="animation-delay: ${index * 0.1}s">
                <div class="card-header">
                    <div>
                        <div class="search-title">${search.title}</div>
                        <span class="search-type">${getSearchTypeLabel(search.type)}</span>
                    </div>
                </div>
                <div class="search-meta">
                    ${search.location ? `📍 ${search.location}` : '🌍 Toutes localisations'}
                    ${search.datePosted ? ` • 📅 ${getDateLabel(search.datePosted)}` : ''}
                </div>
                <div class="card-actions">
                    <button class="btn btn-secondary" onclick="openLink('${search.url}')">
                        🔗 Ouvrir sur LinkedIn
                    </button>
                    <button class="btn btn-secondary btn-small" onclick="copyToClipboard('${escapeHtml(search.url)}')">
                        📋 Copier
                    </button>
                    <button class="btn btn-secondary btn-small" onclick="addToFavorites('${search.id}')">
                        ⭐ Favoris
                    </button>
                </div>
            </div>
        `;
    });
    
    resultsDiv.innerHTML = html;
    showElement('results');
}

function renderHistory() {
    const historyDiv = document.getElementById('history');
    
    if (state.searchHistory.length === 0) {
        historyDiv.innerHTML = getEmptyState('📜', 'Aucun historique', 'Vos recherches passées apparaîtront ici');
        return;
    }

    let html = '<h3 style="margin-bottom: 20px; color: var(--text-primary);">📜 Historique des recherches</h3>';
    
    state.searchHistory.slice(0, 20).forEach(search => {
        html += `
            <div class="search-card">
                <div class="search-title">🔍 ${search.keywords}</div>
                <div class="search-meta">
                    ${search.location ? `📍 ${search.location}` : '🌍 Toutes localisations'}
                    • 🕒 ${formatDate(search.timestamp)}
                </div>
                <div class="card-actions">
                    <button class="btn btn-secondary btn-small" onclick="repeatSearch('${search.id}')">
                        🔄 Répéter
                    </button>
                    <button class="btn btn-secondary btn-small" onclick="deleteFromHistory('${search.id}')">
                        🗑️ Supprimer
                    </button>
                </div>
            </div>
        `;
    });
    
    historyDiv.innerHTML = html;
}

function renderFavorites() {
    const favoritesDiv = document.getElementById('favorites');
    
    if (state.favorites.length === 0) {
        favoritesDiv.innerHTML = getEmptyState('⭐', 'Aucun favori', 'Ajoutez vos recherches favorites pour y accéder rapidement');
        return;
    }

    let html = '<h3 style="margin-bottom: 20px; color: var(--text-primary);">⭐ Recherches favorites</h3>';
    
    state.favorites.forEach(favorite => {
        html += `
            <div class="search-card">
                <div class="search-title">${favorite.title}</div>
                <div class="search-meta">
                    ${favorite.location ? `📍 ${favorite.location}` : '🌍 Toutes localisations'}
                    • ⭐ Ajouté le ${formatDate(favorite.savedAt)}
                </div>
                <div class="card-actions">
                    <button class="btn btn-secondary" onclick="openLink('${favorite.url}')">
                        🔗 Ouvrir
                    </button>
                    <button class="btn btn-secondary btn-small" onclick="removeFromFavorites('${favorite.id}')">
                        ❌ Retirer
                    </button>
                </div>
            </div>
        `;
    });
    
    favoritesDiv.innerHTML = html;
}

// ===========================
// TAB MANAGEMENT
// ===========================
function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target?.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName)?.classList.add('active');
}

function showTabs() {
    const tabsContainer = document.getElementById('tabsContainer');
    const statsContainer = document.getElementById('stats');
    
    tabsContainer.classList.add('active');
    statsContainer.classList.add('active');
}

// ===========================
// FAVORITE MANAGEMENT
// ===========================
function addToFavorites(searchId) {
    const search = state.currentResults.find(s => s.id === searchId);
    
    if (!search) return;
    
    // Check if already in favorites
    if (state.favorites.some(f => f.id === searchId)) {
        showAlert('Cette recherche est déjà dans vos favoris', 'warning');
        return;
    }
    
    // Check limit
    if (state.favorites.length >= CONFIG.MAX_FAVORITES) {
        showAlert(`Vous ne pouvez avoir que ${CONFIG.MAX_FAVORITES} favoris maximum`, 'warning');
        return;
    }
    
    state.favorites.unshift({
        ...search,
        savedAt: new Date().toISOString()
    });
    
    state.stats.savedSearches = state.favorites.length;
    
    saveToStorage();
    updateStats();
    renderFavorites();
    
    showAlert('✅ Ajouté aux favoris !', 'success');
}

function removeFromFavorites(favoriteId) {
    state.favorites = state.favorites.filter(f => f.id !== favoriteId);
    state.stats.savedSearches = state.favorites.length;
    
    saveToStorage();
    updateStats();
    renderFavorites();
    
    showAlert('Retiré des favoris', 'info');
}

// ===========================
// HISTORY MANAGEMENT
// ===========================
function addToHistory(search) {
    state.searchHistory.unshift(search);
    
    // Keep only recent searches
    if (state.searchHistory.length > CONFIG.MAX_HISTORY) {
        state.searchHistory = state.searchHistory.slice(0, CONFIG.MAX_HISTORY);
    }
    
    renderHistory();
}

function deleteFromHistory(searchId) {
    state.searchHistory = state.searchHistory.filter(s => s.id !== searchId);
    saveToStorage();
    renderHistory();
}

function repeatSearch(searchId) {
    const search = state.searchHistory.find(s => s.id === searchId);
    
    if (!search) return;
    
    // Fill form
    document.getElementById('keywords').value = search.keywords;
    document.getElementById('location').value = search.location || '';
    document.getElementById('experience').value = search.experience || '';
    document.getElementById('datePosted').value = search.datePosted || '';
    
    // Scroll to form
    document.querySelector('.search-section').scrollIntoView({ behavior: 'smooth' });
    
    showAlert('Formulaire rempli avec la recherche précédente', 'info');
}

// ===========================
// STATISTICS
// ===========================
function updateStats() {
    document.getElementById('linkCount').textContent = state.stats.linksGenerated;
    document.getElementById('savedSearches').textContent = state.stats.savedSearches;
    document.getElementById('totalSearches').textContent = state.stats.totalSearches;
}

// ===========================
// UTILITY FUNCTIONS
// ===========================
function openLink(url) {
    window.open(url, '_blank', 'noopener,noreferrer');
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => {
            showAlert('✅ Lien copié dans le presse-papiers !', 'success');
        })
        .catch(err => {
            console.error('Copy failed:', err);
            showAlert('❌ Erreur lors de la copie', 'danger');
        });
}

function showLoading(show) {
    const loadingDiv = document.getElementById('loading');
    if (show) {
        loadingDiv.classList.add('active');
    } else {
        loadingDiv.classList.remove('active');
    }
}

function showElement(elementId) {
    document.getElementById(elementId)?.classList.add('active');
}

function hideElement(elementId) {
    document.getElementById(elementId)?.classList.remove('active');
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<strong>${message}</strong>`;
    alert.style.position = 'fixed';
    alert.style.top = '80px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.style.minWidth = '300px';
    alert.style.maxWidth = '500px';
    
    document.body.appendChild(alert);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

function getEmptyState(icon, title, description) {
    return `
        <div class="empty-state">
            <div class="empty-state-icon">${icon}</div>
            <h3 style="color: var(--text-primary); margin-bottom: 10px;">${title}</h3>
            <p style="color: var(--text-secondary);">${description}</p>
        </div>
    `;
}

function getSearchTypeLabel(type) {
    const labels = {
        'primary': 'Principale',
        'alternative': 'Alternative',
        'student': 'Étudiant'
    };
    return labels[type] || 'Personnalisée';
}

function getDateLabel(dateCode) {
    const labels = {
        'r86400': '24h',
        'r604800': '7 jours',
        'r2592000': '30 jours'
    };
    return labels[dateCode] || 'Récent';
}

function formatDate(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'À l\'instant';
    if (diffMins < 60) return `Il y a ${diffMins} min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    if (diffDays < 7) return `Il y a ${diffDays}j`;
    
    return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// ===========================
// EXPORT FUNCTIONALITY
// ===========================
function exportSearches() {
    const dataStr = JSON.stringify({
        history: state.searchHistory,
        favorites: state.favorites,
        stats: state.stats,
        exportDate: new Date().toISOString()
    }, null, 2);
    
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `linkedin-searches-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
    
    showAlert('✅ Données exportées !', 'success');
}

// Make functions globally available
window.generateSearchLinks = generateSearchLinks;
window.toggleTheme = toggleTheme;
window.showTab = showTab;
window.openLink = openLink;
window.copyToClipboard = copyToClipboard;
window.addToFavorites = addToFavorites;
window.removeFromFavorites = removeFromFavorites;
window.deleteFromHistory = deleteFromHistory;
window.repeatSearch = repeatSearch;
window.exportSearches = exportSearches;
