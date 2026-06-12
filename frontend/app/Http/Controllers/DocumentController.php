<?php

namespace App\Http\Controllers;

use App\Models\Document;

class DocumentController extends Controller
{
    public function index()
    {
        $documents = Document::where('user_id', auth()->id())
            ->latest()
            ->get();

        return view('pages.documents', compact('documents'));
    }
}