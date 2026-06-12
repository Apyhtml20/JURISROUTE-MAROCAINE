<?php

namespace App\Http\Controllers;

use App\Models\Conversation;
use App\Models\Document;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;

class ChatController extends Controller
{
    private string $apiBase;

    public function __construct()
    {
        $this->apiBase = config('services.jurisroute.url', 'http://localhost:8000');
    }

    public function index()
    {
        $conversations = auth()->user()
            ->conversations()
            ->latest()
            ->limit(20)
            ->get();

        return view('pages.chat', [
            'conversations' => $conversations,
            'currentConversation' => null,
        ]);
    }

    public function show(int $id)
    {
        $conversation = auth()->user()
            ->conversations()
            ->with('messages')
            ->findOrFail($id);

        $conversations = auth()->user()
            ->conversations()
            ->latest()
            ->limit(20)
            ->get();

        return view('pages.chat', [
            'conversations' => $conversations,
            'currentConversation' => $conversation,
        ]);
    }

    public function send(Request $request)
    {
        $request->validate([
            'message' => 'required|string|max:1000',
            'conversation_id' => 'nullable|integer',
        ]);

        $user = auth()->user();
        $message = $request->input('message');
        $convId = $request->input('conversation_id');

        $conversation = $convId
            ? $user->conversations()->findOrFail($convId)
            : $user->conversations()->create([
                'title' => Str::limit($message, 40),
            ]);

        $conversation->messages()->create([
            'role' => 'user',
            'content' => $message,
        ]);

        try {
            $response = Http::timeout(120)->post("{$this->apiBase}/ask", [
                'question' => $message,
                'lang' => 'auto',
                'use_rag' => true,
            ]);

            if (!$response->successful()) {
                throw new \RuntimeException('Ask endpoint returned HTTP ' . $response->status());
            }

            $data = $response->json();
            $answer = $data['answer'] ?? 'Desole, une erreur est survenue.';
        } catch (\Throwable $e) {
            Log::error('JurisRoute API error: ' . $e->getMessage());
            $answer = 'Le service est temporairement indisponible. Veuillez reessayer.';
        }

        $conversation->messages()->create([
            'role' => 'assistant',
            'content' => $answer,
        ]);

        return response()->json([
            'answer' => $answer,
            'conversation_id' => $conversation->id,
        ]);
    }

    public function upload(Request $request)
    {
        $request->validate([
            'file' => 'required|file|mimes:pdf,jpg,jpeg,png,webp|max:10240',
            'message' => 'nullable|string|max:500',
            'conversation_id' => 'nullable|integer',
        ]);

        $user = auth()->user();
        $file = $request->file('file');
        $convId = $request->input('conversation_id');

        $conversation = $convId
            ? $user->conversations()->findOrFail($convId)
            : $user->conversations()->create([
                'title' => 'Analyse : ' . $file->getClientOriginalName(),
            ]);

        $isPdf = strtolower($file->getClientOriginalExtension()) === 'pdf';
        $endpoint = $isPdf ? '/analyze-pdf' : '/analyze-image';

        try {
            $response = Http::timeout(90)
                ->attach('file', file_get_contents($file->getRealPath()), $file->getClientOriginalName())
                ->post("{$this->apiBase}{$endpoint}");

            if (!$response->successful()) {
                throw new \RuntimeException('Upload endpoint returned HTTP ' . $response->status());
            }

            $data = $response->json();
            $answer = $data['answer'] ?? 'Desole, impossible d\'analyser ce document.';
            $pvInfo = $data['pv_info'] ?? null;
        } catch (\Throwable $e) {
            Log::error('JurisRoute upload error: ' . $e->getMessage());
            $answer = 'Erreur lors de l\'analyse du document.';
            $pvInfo = null;
        }

        Document::create([
            'user_id' => $user->id,
            'conversation_id' => $conversation->id,
            'filename' => $file->getClientOriginalName(),
            'pv_info' => $pvInfo ? json_encode($pvInfo) : null,
        ]);

        $userMsg = $request->input('message')
            ? $request->input('message') . "\n\nDocument joint : " . $file->getClientOriginalName()
            : 'Document soumis : ' . $file->getClientOriginalName();

        $conversation->messages()->create([
            'role' => 'user',
            'content' => $userMsg,
        ]);

        $conversation->messages()->create([
            'role' => 'assistant',
            'content' => $answer,
        ]);

        return response()->json([
            'answer' => $answer,
            'conversation_id' => $conversation->id,
        ]);
    }

    public function destroy(Conversation $conversation)
    {
        if ($conversation->user_id !== auth()->id()) {
            return response()->json(['error' => 'Non autorise'], 403);
        }

        $conversation->messages()->delete();
        $conversation->documents()->delete();
        $conversation->delete();

        return response()->json([
            'success' => true,
            'message' => 'Conversation supprimee',
        ]);
    }
}
