<!DOCTYPE html>
<html lang="fr" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>JurisRoute — @yield('title', 'Authentification')</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Figtree:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=Syne:wght@600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ asset('css/app.css') }}">
    <script>
    /* Restore theme before first paint to prevent flash */
    (function(){var t=localStorage.getItem('jr-theme');if(t)document.documentElement.setAttribute('data-theme',t);})();
    </script>
    <style>
        /* ── Auth page extra polish ── */
        .auth-showcase-copy h1 {
            background: linear-gradient(135deg, #ffffff 0%, rgba(147, 197, 253, 0.92) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .auth-showcase-stats {
            display: flex;
            gap: 28px;
            flex-wrap: wrap;
        }
        .auth-stat {
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        .auth-stat strong {
            font-family: var(--font-display);
            font-size: 1.6rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1;
        }
        .auth-stat span {
            font-size: 0.8rem;
            color: rgba(255,255,255,0.6);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }
        .auth-feature-card {
            padding: 18px 20px 20px;
        }
        .auth-feature-icon {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.12);
            display: grid;
            place-items: center;
            margin-bottom: 12px;
            color: rgba(147, 197, 253, 0.9);
        }
        .auth-panel-card {
            border-radius: var(--radius-md);
        }
        @media (max-width: 1180px) {
            .auth-showcase-stats { gap: 20px; }
            .auth-stat strong { font-size: 1.3rem; }
        }
        @media (prefers-color-scheme: dark) {
            html:not([data-theme="light"]) { --white: #0e1824; }
        }
    </style>
</head>
<body class="auth-body">
<div class="auth-shell">

    {{-- ── Left showcase ───────────────────────────── --}}
    <section class="auth-showcase">
        <div class="auth-showcase-layer"></div>
        <div class="auth-showcase-content">

            <a href="{{ route('login') }}" class="brand-link brand-link-light">
                <img class="brand-logo-image auth-logo-image"
                     src="{{ asset('images/jurisroute-logo-dark.svg?v=5') }}"
                     alt="JurisRoute">
            </a>

            <div class="auth-showcase-copy">
                <h1>Comprendre une amende, vérifier une procédure et agir rapidement.</h1>
                <p>Un espace simple pour poser vos questions, analyser un PV et retrouver vos échanges.</p>
            </div>

            <div class="auth-showcase-stats">
                <div class="auth-stat">
                    <strong>52-05</strong>
                    <span>Loi de référence</span>
                </div>
                <div class="auth-stat">
                    <strong>PDF + Image</strong>
                    <span>Formats analysés</span>
                </div>
                <div class="auth-stat">
                    <strong>FR / AR</strong>
                    <span>Langues supportées</span>
                </div>
            </div>

            <div class="auth-feature-grid">
                <div class="auth-feature-card">
                    <div class="auth-feature-icon">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                    </div>
                    <strong>Analyse guidée</strong>
                    <span>Chargez un PV ou une photo et obtenez une lecture structurée.</span>
                </div>
                <div class="auth-feature-card">
                    <div class="auth-feature-icon">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    </div>
                    <strong>Démarches simplifiées</strong>
                    <span>Retrouvez les sanctions, recours et pièces utiles sans jargon.</span>
                </div>
                <div class="auth-feature-card">
                    <div class="auth-feature-icon">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    </div>
                    <strong>Historique clair</strong>
                    <span>Retrouvez vos conversations précédentes sans navigation compliquée.</span>
                </div>
            </div>

        </div>
    </section>

    {{-- ── Right panel ─────────────────────────────── --}}
    <section class="auth-panel-right">
        <div class="auth-panel-card">
            @yield('content')
        </div>
    </section>

</div>

<script src="{{ asset('js/app.js') }}"></script>
<script>
window.togglePassword = function (id) {
    var el = document.getElementById(id);
    if (!el) return;
    el.type = el.type === 'password' ? 'text' : 'password';
};
</script>
</body>
</html>
