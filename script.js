// ============================================
// STATE & TRANSLATIONS
// ============================================
let currentFilter = 'all';
let activeCoupon = null;
let pollInterval = null;
let currentLanguage = localStorage.getItem('site_lang') || 'en';
let translationsData = {};

async function loadTranslations() {
    try {
        const res = await fetch('/data/translations.json');
        if (res.ok) {
            translationsData = await res.json();
            applyLanguage(currentLanguage);
        }
    } catch (e) {
        console.warn('Could not load translations:', e.message);
    }
}

function applyLanguage(lang) {
    if (!lang) return;
    currentLanguage = lang;
    localStorage.setItem('site_lang', lang);

    const langCodeEl = document.getElementById('langCurrentCode');
    if (langCodeEl) langCodeEl.textContent = lang.toUpperCase();

    document.querySelectorAll('.lang-item').forEach(item => {
        item.classList.toggle('active', item.dataset.lang === lang);
    });

    const dict = translationsData[lang] || translationsData['en'] || {};

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = dict[key];
            } else {
                el.textContent = dict[key];
            }
        }
    });

    const searchInput = document.getElementById('searchInput');
    if (searchInput && dict['search_placeholder']) {
        searchInput.placeholder = dict['search_placeholder'];
    }
}