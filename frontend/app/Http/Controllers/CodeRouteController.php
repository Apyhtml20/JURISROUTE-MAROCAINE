<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class CodeRouteController extends Controller
{
    public function index()
    {
        return view('pages.code-route');
    }
}