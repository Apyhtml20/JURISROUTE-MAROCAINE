@extends('layouts.app')
@section('title', 'Document officiel')

@section('content')
<div class="documents-container">
    <section class="hero-panel hero-panel-tight">
        <div class="hero-copy">
            <h1>Consultez le document officiel du code de la route.</h1>
            <p>Cette page permet aux citoyens de lire directement le document officiel de conduite et de verifier les regles, sanctions et procedures avant de poser une question dans le chat.</p>
        </div>
        <div class="hero-side">
            <div class="mini-stat-grid">
                <div class="mini-stat">
                    <strong>Loi 52-05</strong>
                    <span>Base legale consultable</span>
                </div>
                <div class="mini-stat">
                    <strong>PDF</strong>
                    <span>Lecture et telechargement</span>
                </div>
            </div>
            <a href="{{ asset('pdf/Code_de_la_Route.pdf') }}" download class="btn-primary btn-full">
                Telecharger le document
            </a>
        </div>
    </section>

    <div class="pdf-layout pdf-layout-clean">
        <aside class="pdf-sidebar pdf-sidebar-clean">
            <div class="pdf-sidebar-header">Acces rapide</div>
            <div class="pdf-toc">
                <a href="{{ asset('pdf/Code_de_la_Route.pdf') }}" target="_blank" class="pdf-toc-btn">Ouvrir dans un nouvel onglet</a>
                <a href="{{ route('chat.index') }}" class="pdf-toc-btn">Retourner au chat</a>
                <a href="{{ route('documents.index') }}" class="pdf-toc-btn">Inserer un document a analyser</a>
            </div>
        </aside>

        <div class="pdf-main pdf-main-clean">
            <div class="pdf-toolbar">
                <div class="pdf-title">Document officiel de conduite</div>
                <a href="{{ asset('pdf/Code_de_la_Route.pdf') }}" download class="pdf-btn pdf-btn-dl">Telecharger</a>
            </div>

            <div class="official-doc-frame">
                <iframe
                    src="{{ asset('pdf/Code_de_la_Route.pdf') }}"
                    title="Code de la route"
                    class="official-doc-iframe">
                </iframe>
            </div>
        </div>
    </div>
</div>
@endsection
