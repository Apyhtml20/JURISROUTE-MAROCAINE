@extends('layouts.app')
@section('title', 'Documents')

@section('content')
<div class="documents-container">
    <section class="hero-panel hero-panel-tight">
        <div class="hero-copy">
            <span class="eyebrow">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                Mes documents
            </span>
            <h1>Centralisez vos pièces et retrouvez rapidement chaque analyse.</h1>
            <p>Votre espace conserve les documents transmis, les informations extraites et les liens directs vers les conversations associées. L'objectif est de rendre la lecture administrative plus simple et plus claire.</p>
        </div>
        <div class="hero-side">
            <div class="mini-stat-grid">
                <div class="mini-stat">
                    <strong>{{ $documents->count() }}</strong>
                    <span>Documents enregistrés</span>
                </div>
                <div class="mini-stat">
                    <strong>PDF / Image</strong>
                    <span>Formats pris en charge</span>
                </div>
            </div>
            <label class="btn-primary btn-full" style="cursor:pointer;" id="uploadLabel">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Ajouter un document
                <input type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" hidden onchange="analyzeDoc(this)" id="docFileInput">
            </label>
        </div>
    </section>

    <div id="uploadProgress" class="upload-progress hidden">
        <div class="progress-bar"><div class="progress-fill"></div></div>
        <span>Analyse du document en cours&hellip; Cela peut prendre quelques secondes.</span>
    </div>

    @if($documents->isEmpty())
    <div class="documents-empty">
        <div style="width:72px;height:72px;border-radius:20px;background:var(--gold-soft);color:var(--gold);display:grid;place-items:center;margin:0 auto 18px;">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="13" x2="12" y2="17"/><line x1="10" y1="15" x2="14" y2="15"/></svg>
        </div>
        <h3>Aucun document analysé pour le moment</h3>
        <p>Importez un PV, une photo ou un justificatif routier. JurisRoute ouvrira automatiquement une conversation pour analyser le contenu et vous guider.</p>
    </div>
    @else
    <div class="documents-grid">
        @foreach($documents as $doc)
        <article class="doc-card">
            <div class="doc-card-head">
                <div class="doc-card-icon">
                    @if(in_array(strtolower(pathinfo($doc->filename, PATHINFO_EXTENSION)), ['jpg', 'jpeg', 'png', 'webp']))
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                    @else
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    @endif
                </div>
                <span class="pv-tag">Analyse archivée</span>
            </div>

            <div>
                <div class="doc-filename">{{ $doc->filename }}</div>
                <div class="doc-date">Ajouté le {{ $doc->created_at->format('d/m/Y') }} à {{ $doc->created_at->format('H:i') }}</div>
            </div>

            @if($doc->pv_info)
            <div class="doc-pv-info">
                @foreach(json_decode($doc->pv_info, true) ?? [] as $k => $v)
                    @if($v)
                    <span class="pv-tag">{{ $k }} : {{ $v }}</span>
                    @endif
                @endforeach
            </div>
            @endif

            @if($doc->conversation_id)
            <a href="{{ route('chat.show', $doc->conversation_id) }}" class="doc-card-link btn-secondary" style="font-size:.88rem;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                Voir l'analyse associée
            </a>
            @endif
        </article>
        @endforeach
    </div>
    @endif
</div>
@endsection

@push('scripts')
<script>
const CSRF = document.querySelector('meta[name="csrf-token"]').content;

async function analyzeDoc(input) {
    var file = input.files[0];
    if (!file) return;

    var allowed = ['application/pdf', 'image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
    if (!allowed.includes(file.type)) {
        toast('Format non supporté. Utilisez PDF, JPG, PNG ou WebP.', 'error');
        return;
    }
    if (file.size > 20 * 1024 * 1024) {
        toast('Fichier trop volumineux (max 20 Mo).', 'error');
        return;
    }

    document.getElementById('uploadProgress').classList.remove('hidden');
    document.getElementById('uploadLabel').style.pointerEvents = 'none';
    document.getElementById('uploadLabel').style.opacity = '0.7';

    var formData = new FormData();
    formData.append('file', file);
    formData.append('_token', CSRF);

    try {
        var res  = await fetch('/chat/upload', { method: 'POST', body: formData });
        var data = await res.json();

        if (!res.ok) {
            toast(data.error || 'Erreur lors de l\'analyse du document.', 'error');
            document.getElementById('uploadProgress').classList.add('hidden');
            document.getElementById('uploadLabel').style.pointerEvents = '';
            document.getElementById('uploadLabel').style.opacity = '';
            return;
        }

        if (data.conversation_id) {
            toast('Document analysé avec succès. Redirection…', 'success', null, 1800);
            setTimeout(function () {
                window.location.href = '/chat/' + data.conversation_id;
            }, 900);
        } else {
            document.getElementById('uploadProgress').classList.add('hidden');
            document.getElementById('uploadLabel').style.pointerEvents = '';
            document.getElementById('uploadLabel').style.opacity = '';
            toast('Document reçu mais sans conversation associée.', 'warning');
        }
    } catch (e) {
        document.getElementById('uploadProgress').classList.add('hidden');
        document.getElementById('uploadLabel').style.pointerEvents = '';
        document.getElementById('uploadLabel').style.opacity = '';
        toast('Erreur réseau lors de l\'envoi du document.', 'error');
    }
}
</script>
@endpush
