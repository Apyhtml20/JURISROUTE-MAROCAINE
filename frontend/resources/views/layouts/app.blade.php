<!DOCTYPE html>
<html lang="fr" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>JurisRoute — @yield('title', 'Plateforme')</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Figtree:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=Syne:wght@600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ asset('css/app.css') }}">
    @stack('styles')
    <script>
    /* Restore theme before first paint to prevent flash */
    (function(){var t=localStorage.getItem('jr-theme');if(t)document.documentElement.setAttribute('data-theme',t);})();
    </script>
</head>
<body>

{{-- Toast container --}}
<div id="toast-container" aria-live="polite" aria-atomic="false"></div>

<div class="site-context-bg" aria-hidden="true">
    <div class="bg-soft-orb bg-soft-orb-a"></div>
    <div class="bg-soft-orb bg-soft-orb-b"></div>
    <div class="bg-road-sweep"></div>
    <div class="bg-road-markings"></div>
    <div class="bg-card-pattern bg-card-pattern-a">PV</div>
    <div class="bg-card-pattern bg-card-pattern-b">52-05</div>
    <div class="bg-road-car" aria-hidden="true">
        <svg class="car-svg" viewBox="0 0 240 110" fill="none" xmlns="http://www.w3.org/2000/svg">
            <ellipse class="car-headlight-glow" cx="228" cy="76" rx="18" ry="10"/>
            <path class="car-body" d="M8 80 L8 64 Q8 58 14 58 L58 58 L80 32 L160 32 L182 58 L226 58 Q232 58 232 64 L232 80 Q232 86 226 86 L14 86 Q8 86 8 80 Z"/>
            <path class="car-glass" d="M86 58 L104 36 L156 36 L174 58 Z"/>
            <path class="car-glass car-glass-rear" d="M62 58 L82 36 L104 36 L86 58 Z"/>
            <circle class="car-wheel-arch" cx="68" cy="86" r="20"/>
            <circle class="car-wheel-arch" cx="172" cy="86" r="20"/>
            <circle class="car-wheel" cx="68" cy="86" r="14"/>
            <circle class="car-wheel-center" cx="68" cy="86" r="5"/>
            <circle class="car-wheel" cx="172" cy="86" r="14"/>
            <circle class="car-wheel-center" cx="172" cy="86" r="5"/>
            <line class="car-detail" x1="86" y1="58" x2="86" y2="84" stroke-width="1.2"/>
            <rect class="car-taillight" x="8" y="64" width="7" height="11" rx="2"/>
            <rect class="car-headlight-body" x="225" y="64" width="7" height="10" rx="2"/>
        </svg>
    </div>
</div>

<header class="app-header app-header-pro">
    <div class="header-brand">
        <a href="{{ route('chat.index') }}" class="brand-link" aria-label="Accueil JurisRoute">
            <img class="brand-logo-image brand-logo-light" src="{{ asset('images/jurisroute-logo-light.svg?v=5') }}" alt="JurisRoute">
            <img class="brand-logo-image brand-logo-dark"  src="{{ asset('images/jurisroute-logo-dark.svg?v=5') }}"  alt="" aria-hidden="true">
        </a>
    </div>

    <nav class="top-nav-actions" aria-label="Navigation principale">
        <a href="{{ route('chat.index') }}" class="top-nav-link {{ request()->routeIs('chat.*') ? 'active' : '' }}">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            Chat
        </a>
        <a href="{{ route('documents.index') }}" class="top-nav-link {{ request()->routeIs('documents.*') ? 'active' : '' }}">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            Documents
        </a>
        <a href="{{ route('code-route.index') }}" class="top-nav-link {{ request()->routeIs('code-route.*') ? 'active' : '' }}">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
            Code de la route
        </a>
        <a href="{{ route('profile.index') }}" class="top-nav-link {{ request()->routeIs('profile.*') ? 'active' : '' }}">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            Mon compte
        </a>
    </nav>

    <div class="header-actions">
        {{-- Dark mode toggle --}}
        <button id="darkToggle" class="dark-toggle" aria-label="Basculer le thème sombre" title="Mode sombre / clair">
            <svg class="icon-moon" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            <svg class="icon-sun"  width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
        </button>

        <div class="header-user simple-user-menu">
            <div class="user-meta user-meta-minimal">
                <span class="user-name">{{ auth()->user()->name }}</span>
                <span class="user-kicker">Compte citoyen</span>
            </div>
            <form method="POST" action="{{ route('logout') }}">
                @csrf
                <button class="logout-btn" type="submit">Déconnexion</button>
            </form>
        </div>
    </div>
</header>

<main class="app-main">
    @yield('content')
</main>

{{-- Markdown renderer (CDN) --}}
<script src="https://cdn.jsdelivr.net/npm/marked@9.1.6/marked.min.js"></script>
<script src="{{ asset('js/app.js') }}"></script>

<script>
/* ── Dark mode ────────────────────────────────────────────── */
(function () {
    const root = document.documentElement;
    const btn  = document.getElementById('darkToggle');
    const saved = localStorage.getItem('jr-theme');
    if (saved) root.setAttribute('data-theme', saved);

    btn && btn.addEventListener('click', function () {
        const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', next);
        localStorage.setItem('jr-theme', next);
    });
})();

/* ── Toast system ─────────────────────────────────────────── */
window.toast = function (msg, type, title, duration) {
    type     = type     || 'info';
    duration = (duration === undefined) ? 4200 : duration;

    var icons = {
        success: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>',
        error:   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        info:    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
        warning: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    };
    var labels = { success: 'Succès', error: 'Erreur', info: 'Information', warning: 'Attention' };

    var container = document.getElementById('toast-container');
    if (!container) return;

    var el = document.createElement('div');
    el.className = 'toast toast-' + type;
    el.setAttribute('role', 'alert');
    el.innerHTML =
        '<div class="toast-icon">' + (icons[type] || icons.info) + '</div>' +
        '<div class="toast-body">' +
            '<div class="toast-title">' + (title || labels[type] || 'Notification') + '</div>' +
            '<div class="toast-msg">'  + msg + '</div>' +
        '</div>' +
        '<button class="toast-close" aria-label="Fermer">' +
            '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
        '</button>';

    function dismiss() {
        el.classList.add('toast-out');
        setTimeout(function () { el.remove(); }, 260);
    }

    el.querySelector('.toast-close').addEventListener('click', dismiss);
    container.appendChild(el);
    if (duration > 0) setTimeout(dismiss, duration);
    return el;
};

/* ── Password toggle helper ───────────────────────────────── */
window.togglePassword = function (id) {
    var el = document.getElementById(id);
    if (!el) return;
    el.type = el.type === 'password' ? 'text' : 'password';
};
</script>

@stack('scripts')
</body>
</html>
