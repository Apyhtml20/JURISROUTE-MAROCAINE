@extends('layouts.app')
@section('title', 'Chat')

@section('content')
<div class="chat-page">
    <div class="chat-layout simple-chat-layout">

        {{-- ── Sidebar ─────────────────────────────────── --}}
        <aside class="chat-sidebar">
            <div class="sidebar-top">
                <div class="sidebar-summary-card">
                    <div class="sidebar-summary-title">Vue rapide</div>
                    <p>Accédez à votre historique et relancez une nouvelle demande en quelques secondes.</p>
                </div>
                <button class="btn-primary btn-full" type="button" onclick="newConversation()">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    Nouvelle conversation
                </button>
            </div>

            @if($conversations->count() > 0)
            <div class="sidebar-section">
                <div class="sidebar-label">Historique &mdash; {{ $conversations->count() }}</div>
                <div class="conversation-list">
                    @foreach($conversations as $conv)
                    @php $isActive = $currentConversation && $currentConversation->id === $conv->id; @endphp
                    <div @class(['conv-item-wrap', 'active' => $isActive]) data-id="{{ $conv->id }}">
                        <a href="{{ route('chat.show', $conv) }}" class="conv-item-link">
                            <div class="conv-title">{{ Str::limit($conv->title, 34) }}</div>
                            <div class="conv-time">{{ $conv->created_at->diffForHumans() }}</div>
                        </a>
                        <button class="conv-delete-btn" type="button" onclick="deleteConv({{ $conv->id }}, this)" title="Supprimer cette conversation">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>
                        </button>
                    </div>
                    @endforeach
                </div>
            </div>
            @endif
        </aside>

        {{-- ── Chat area ───────────────────────────────── --}}
        <section class="chat-area"
            data-conv-id="{{ $currentConversation?->id ?? '' }}"
            data-initial="{{ strtoupper(substr(auth()->user()->name, 0, 1)) }}"
            id="chatArea">
            <div class="chat-panel-header">
                <div class="chat-panel-copy">
                    <h1>Assistant administratif</h1>
                    <p>Posez votre question sur une amende, un PV ou une démarche routière.</p>
                </div>
                <div class="chat-header-actions">
                    <button class="panel-action-btn" type="button" onclick="document.getElementById('fileInput').click()">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                        Joindre un document
                    </button>
                </div>
            </div>

            <div class="messages-container chat-stream" id="messagesContainer">
                @if(!$currentConversation || $currentConversation->messages->isEmpty())
                <div class="chat-empty" id="chatEmpty">
                    <h3>Commencez une conversation</h3>
                    <p>Écrivez votre question ou ajoutez un document pour obtenir une réponse claire et structurée.</p>
                    <div class="empty-helper-grid">
                        <div class="empty-helper-card">
                            <strong>Pour bien démarrer</strong>
                            <span>Indiquez le type d'infraction, la date et ce que vous souhaitez vérifier.</span>
                        </div>
                        <div class="empty-helper-card">
                            <strong>Documents utiles</strong>
                            <span>PV, photo, avis d'amende ou capture du document officiel.</span>
                        </div>
                    </div>
                    <div class="empty-suggestions">
                        @foreach(['Comment contester un PV ?', 'Quelle amende pour excès de vitesse ?', 'Que vérifier sur un procès-verbal ?', 'Sanction pour téléphone au volant ?'] as $s)
                        <button class="empty-suggestion" type="button" onclick="sendSuggestion('{{ $s }}')">{{ $s }}</button>
                        @endforeach
                    </div>
                </div>
                @else
                    @foreach($currentConversation->messages as $msg)
                    <div class="message message-{{ $msg->role }}">
                        @if($msg->role === 'assistant')
                        <div class="message-avatar assistant-avatar">
                            <span>JR</span>
                        </div>
                        @endif
                        <div class="message-bubble">
                            @if($msg->role === 'assistant')
                            <div class="message-content md-content">{!! \Illuminate\Support\Str::of($msg->content)->markdown() !!}</div>
                            @else
                            <div class="message-content">{!! nl2br(e($msg->content)) !!}</div>
                            @endif
                            <div class="message-time">{{ $msg->created_at->format('H:i') }}</div>
                        </div>
                        @if($msg->role === 'user')
                        <div class="message-avatar user-avatar-sm">{{ strtoupper(substr(auth()->user()->name, 0, 1)) }}</div>
                        @endif
                    </div>
                    @endforeach
                @endif

                <div id="typingIndicator" class="typing-indicator hidden">
                    <div class="message-avatar assistant-avatar"><span>JR</span></div>
                    <div class="typing-bubble"><span></span><span></span><span></span></div>
                </div>
            </div>

            <div class="chat-input-area">
                <div class="chat-input-wrapper">
                    <textarea
                        id="chatInput"
                        placeholder="Exemple : J'ai reçu une amende et je veux savoir si je peux la contester…"
                        rows="1"
                        onkeydown="handleKey(event)"
                        oninput="autoResize(this); updateCounter(this)"
                        maxlength="1000"
                    ></textarea>
                    <div class="input-actions">
                        <label class="attach-btn" title="Joindre un document (PDF, JPG, PNG)">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                            <span>Joindre</span>
                            <input type="file" id="fileInput" accept=".pdf,.jpg,.jpeg,.png,.webp" hidden onchange="handleFile(this)">
                        </label>
                        <span class="input-counter" id="inputCounter"></span>
                        <button class="send-btn" type="button" onclick="sendMessage()" aria-label="Envoyer le message">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                        </button>
                    </div>
                </div>
                <div id="filePreview" class="file-preview hidden"></div>
                <p class="input-hint">
                    Appuyez sur <kbd>Entrée</kbd> pour envoyer &middot; <kbd>Maj + Entrée</kbd> pour sauter une ligne
                </p>
            </div>
        </section>
    </div>
</div>
@endsection

@push('scripts')
<script>
/* Read initial state from data attributes to avoid Blade-in-JS lint errors */
var _ca = document.getElementById('chatArea');
let currentConversationId = _ca.dataset.convId ? parseInt(_ca.dataset.convId, 10) : null;
const CSRF    = document.querySelector('meta[name="csrf-token"]').content;
const INITIAL = _ca.dataset.initial || '?';
let pendingFile = null;

/* ── Textarea helpers ────────────────────────────── */

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

function updateCounter(el) {
    var counter = document.getElementById('inputCounter');
    if (!counter) return;
    var len  = el.value.length;
    var max  = parseInt(el.getAttribute('maxlength') || 1000);
    var left = max - len;
    if (left > 150) { counter.textContent = ''; counter.className = 'input-counter'; return; }
    counter.textContent = left + ' restants';
    counter.className = 'input-counter' + (left < 50 ? ' limit' : left < 150 ? ' warn' : '');
}

function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

/* ── Suggestion click ────────────────────────────── */

function sendSuggestion(text) {
    var input = document.getElementById('chatInput');
    input.value = text;
    autoResize(input);
    sendMessage();
}

/* ── File handling ───────────────────────────────── */

function handleFile(input) {
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

    pendingFile = file;
    var ext = file.name.split('.').pop().toUpperCase();
    var preview = document.getElementById('filePreview');
    preview.innerHTML =
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>' +
        '<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escapeHtml(file.name) + '</span>' +
        '<span style="font-size:.76rem;opacity:.7;flex-shrink:0;">' + ext + '</span>' +
        '<button type="button" onclick="removeFile()" title="Retirer le fichier" style="margin-left:4px;">' +
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
        '</button>';
    preview.classList.remove('hidden');
}

function removeFile() {
    pendingFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('filePreview').classList.add('hidden');
}

/* ── Send message ────────────────────────────────── */

async function sendMessage() {
    var input = document.getElementById('chatInput');
    var text  = input.value.trim();
    if (!text && !pendingFile) return;

    document.getElementById('chatEmpty')?.remove();
    appendMsg('user', text || ('Document joint : ' + pendingFile.name));
    input.value = '';
    input.style.height = 'auto';
    updateCounter(input);
    showTyping(true);

    try {
        var res;
        if (pendingFile) {
            var fd = new FormData();
            fd.append('file', pendingFile);
            if (text) fd.append('message', text);
            if (currentConversationId) fd.append('conversation_id', currentConversationId);
            fd.append('_token', CSRF);
            res = await fetch('/chat/upload', { method: 'POST', body: fd });
        } else {
            res = await fetch('/chat/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': CSRF },
                body: JSON.stringify({ message: text, conversation_id: currentConversationId })
            });
        }

        var data = await res.json();
        showTyping(false);

        if (!res.ok) {
            toast(data.error || 'Une erreur est survenue. Veuillez réessayer.', 'error');
            appendMsg('assistant', 'Désolé, une erreur est survenue. Veuillez réessayer.');
        } else {
            appendMsg('assistant', data.answer || 'Aucune réponse reçue.');
            if (data.conversation_id && !currentConversationId) {
                currentConversationId = data.conversation_id;
                history.replaceState({}, '', '/chat/' + data.conversation_id);
            }
        }
        removeFile();
    } catch (e) {
        showTyping(false);
        appendMsg('assistant', 'Impossible de contacter le serveur. Vérifiez votre connexion.');
        toast('Connexion impossible au serveur.', 'error');
    }

    scrollBot();
}

/* ── Append message ──────────────────────────────── */

function appendMsg(role, content) {
    var container = document.getElementById('messagesContainer');
    var now = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    var div = document.createElement('div');
    div.className = 'message message-' + role;

    var bubbleContent;
    if (role === 'assistant') {
        var rendered = (typeof marked !== 'undefined')
            ? marked.parse(content)
            : escapeHtml(content).replace(/\n/g, '<br>');
        bubbleContent =
            '<div class="message-avatar assistant-avatar"><span>JR</span></div>' +
            '<div class="message-bubble">' +
                '<div class="message-content md-content">' + rendered + '</div>' +
                '<div class="message-time">' + now + '</div>' +
            '</div>';
    } else {
        bubbleContent =
            '<div class="message-bubble">' +
                '<div class="message-content">' + escapeHtml(content).replace(/\n/g, '<br>') + '</div>' +
                '<div class="message-time">' + now + '</div>' +
            '</div>' +
            '<div class="message-avatar user-avatar-sm">' + INITIAL + '</div>';
    }

    div.innerHTML = bubbleContent;
    container.insertBefore(div, document.getElementById('typingIndicator'));
    scrollBot();
}

/* ── Helpers ─────────────────────────────────────── */

function escapeHtml(value) {
    var div = document.createElement('div');
    div.textContent = value;
    return div.innerHTML;
}

function showTyping(show) {
    document.getElementById('typingIndicator').classList.toggle('hidden', !show);
    scrollBot();
}

function scrollBot() {
    var c = document.getElementById('messagesContainer');
    requestAnimationFrame(function () {
        c.scrollTo({ top: c.scrollHeight, behavior: 'smooth' });
    });
}

function newConversation() {
    window.location.href = '/chat';
}

/* ── Delete conversation ─────────────────────────── */

async function deleteConv(id, btn) {
    if (!confirm('Supprimer cette conversation ? Cette action est irréversible.')) return;

    var wrap = btn.closest('.conv-item-wrap');
    wrap.style.opacity = '0.5';
    wrap.style.pointerEvents = 'none';

    try {
        var res  = await fetch('/chat/' + id, {
            method: 'DELETE',
            headers: {
                'X-CSRF-TOKEN': CSRF,
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        var data = await res.json();

        if (res.ok && data.success) {
            wrap.style.transition = 'opacity .2s, transform .2s';
            wrap.style.opacity = '0';
            wrap.style.transform = 'translateX(-10px)';
            setTimeout(function () { wrap.remove(); }, 220);
            toast('Conversation supprimée.', 'success');
            if (currentConversationId === id) window.location.href = '/chat';
        } else {
            wrap.style.opacity = '1';
            wrap.style.pointerEvents = '';
            toast(data.error || 'Impossible de supprimer cette conversation.', 'error');
        }
    } catch (e) {
        wrap.style.opacity = '1';
        wrap.style.pointerEvents = '';
        toast('Erreur réseau lors de la suppression.', 'error');
    }
}

/* ── Init ────────────────────────────────────────── */

window.addEventListener('load', function () {
    scrollBot();
    /* Configure marked.js for safe rendering */
    if (typeof marked !== 'undefined') {
        marked.setOptions({ breaks: true, gfm: true });
    }
});
</script>
@endpush
