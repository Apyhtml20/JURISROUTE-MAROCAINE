@extends('layouts.app')
@section('title', 'Compte')

@section('content')
<div class="profile-container">
    <div class="profile-header">
        <div>
            <h1>Mon compte</h1>
            <p>Gerez vos informations personnelles, vos acces et la securite de votre espace.</p>
        </div>
    </div>

    @if (session('success'))
        <div class="alert alert-success">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            {{ session('success') }}
        </div>
    @endif

    @if ($errors->any())
        <div class="alert alert-error">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            {{ $errors->first() }}
        </div>
    @endif

    <section class="profile-summary">
        <div class="profile-card">
            <div class="profile-card-header">
                <div class="profile-avatar">{{ strtoupper(substr(auth()->user()->name, 0, 1)) }}</div>
                <div class="profile-info">
                    <div class="profile-name">{{ auth()->user()->name }}</div>
                    <div class="profile-email">{{ auth()->user()->email }}</div>
                    <div class="profile-badge">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                        Espace personnel actif
                    </div>
                </div>
            </div>

            <div class="profile-stats">
                <div class="profile-stat">
                    <strong>Securise</strong>
                    <span>Acces protege par mot de passe</span>
                </div>
                <div class="profile-stat">
                    <strong>Documente</strong>
                    <span>Historique des analyses conserve</span>
                </div>
                <div class="profile-stat">
                    <strong>Prive</strong>
                    <span>Conversations liees a votre compte</span>
                </div>
            </div>
        </div>

        <div class="profile-card">
            <h2>Bonnes pratiques</h2>
            <div class="timeline-list" style="margin-top:16px;">
                <div class="timeline-item">
                    <div class="timeline-index">1</div>
                    <div>
                        <strong>Verifiez votre email</strong>
                        <p>Utilisez une adresse que vous consultez regulierement pour les notifications importantes.</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-index">2</div>
                    <div>
                        <strong>Choisissez un mot de passe robuste</strong>
                        <p>Melangez lettres, chiffres et caracteres speciaux pour proteger votre espace.</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-index">3</div>
                    <div>
                        <strong>Conservez vos documents</strong>
                        <p>Ajoutez des PV lisibles afin de faciliter les analyses et les recours.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <div class="profile-card">
        <h2 style="margin-bottom:18px;">Informations personnelles</h2>
        <form method="POST" action="{{ route('profile.update') }}" class="profile-form">
            @csrf
            @method('PATCH')

            <div class="form-row">
                <div class="form-group">
                    <label for="name">Nom complet</label>
                    <input type="text" id="name" name="name" value="{{ old('name', auth()->user()->name) }}" required>
                </div>
                <div class="form-group">
                    <label for="email">Adresse email</label>
                    <input type="email" id="email" name="email" value="{{ old('email', auth()->user()->email) }}" required>
                </div>
            </div>

            <div class="form-actions">
                <button type="submit" class="btn-primary">Enregistrer les modifications</button>
            </div>
        </form>
    </div>

    <div class="profile-card">
        <h2 style="margin-bottom:18px;">Securite du compte</h2>
        <form method="POST" action="{{ route('profile.password') }}" class="profile-form">
            @csrf
            @method('PUT')

            <div class="form-group">
                <label for="current_password">Mot de passe actuel</label>
                <div class="input-wrapper">
                    <input type="password" id="current_password" name="current_password" required>
                    <button type="button" class="input-toggle" onclick="togglePassword('current_password')">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="new_password">Nouveau mot de passe</label>
                    <div class="input-wrapper">
                        <input type="password" id="new_password" name="new_password" required>
                        <button type="button" class="input-toggle" onclick="togglePassword('new_password')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        </button>
                    </div>
                </div>
                <div class="form-group">
                    <label for="new_password_confirmation">Confirmation</label>
                    <input type="password" id="new_password_confirmation" name="new_password_confirmation" required>
                </div>
            </div>

            <div class="form-actions">
                <button type="submit" class="btn-primary">Mettre a jour le mot de passe</button>
            </div>
        </form>
    </div>

    <div class="profile-card profile-card-danger">
        <h2>Suppression du compte</h2>
        <p>Cette action supprime l'acces a votre espace personnel et reste irreversible.</p>
        <form method="POST" action="{{ route('profile.destroy') }}" onsubmit="return confirm('Etes-vous sur de vouloir supprimer votre compte ? Cette action est irreversible.')" style="margin-top:18px;">
            @csrf
            @method('DELETE')
            <button type="submit" class="btn-danger">Supprimer mon compte</button>
        </form>
    </div>
</div>
@endsection
