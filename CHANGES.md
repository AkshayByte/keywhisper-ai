# Changes Made to EM-SEC Project

> **Contributor:** AkshayByte
> **Date:** May 2026
> **Type:** Open-source bug fix contribution to a peer's research project
> **Original Repo:** https://github.com/HerambKataru/ai-based-side-channel-attack-on-keyboard
> **My Fork:** https://github.com/AkshayByte/keywhisper-ai

---

## Overview

I reviewed my friend's **EM-SEC** codebase — an AI-powered electromagnetic
side-channel attack research platform — and identified three issues: two backend
crash vulnerabilities and a UI anti-pattern freezing the live spectrogram. Fixed
all three with minimal, scoped changes. Zero modifications to core ML logic,
signal processing, or UI design.

---

## File-by-File Changes

---

### 1. `app.py` — Backend Error Handling

**Status:** Modified

#### What was wrong (before my fix):

```python
# BEFORE — No error guard. Unknown page = Flask debug traceback shown to user
@app.route('/<page>')
def pages(page):
    return render_template(f'{page}')   # crashes with TemplateNotFound

# BEFORE — No file validation. Missing file = KeyError crash = 500 error
@app.route('/api/upload', methods=['POST'])
def api_upload():
    f = request.files['file']           # KeyError if no file attached
    f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
    return jsonify({'msg': 'File Ingested for Analysis'})
```

#### What I changed (after my fix):

```python
# AFTER — TemplateNotFound is caught, clean 404 JSON returned
from jinja2 import TemplateNotFound   # <-- added import

@app.route('/<page>')
def pages(page):
    try:
        return render_template(f'{page}')
    except TemplateNotFound:
        return jsonify({'error': f'Page "{page}" not found'}), 404

# AFTER — Full file validation before touching the filesystem
@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files or request.files['file'].filename == '':
        return jsonify({'error': 'No file selected. Please attach a file to the request.'}), 400
    f = request.files['file']
    filename = secure_filename(f.filename)
    if not filename:
        return jsonify({'error': 'Invalid filename after sanitization.'}), 400
    f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({'msg': f'File "{filename}" ingested for analysis'})
```

**Lines changed:** ~15 lines added, 4 lines replaced

---

### 2. `static/js/main.js` — Toast System & Fetch Error Handling

**Status:** Modified (full rewrite of the file, same logic + improvements)

#### What was wrong (before my fix):

```javascript
// BEFORE — 3 separate alert() calls that freeze the browser tab
// (the spectrogram animation stops while any alert is open)
alert("Data Ingested Successfully!");   // line 88
alert(res.error);                       // line 104
alert("Model Training Finished!");      // line 118

// BEFORE — fetch() chains with no .catch() — network errors silently kill the loop
fetch('/api/spectrogram')
    .then(r => r.json())
    .then(res => { /* draw */ });
    // ↑ no .catch() — if server is unreachable, animation dies silently
```

#### What I changed (after my fix):

```javascript
// AFTER — Non-blocking toast notification system (added at top of file)
function showToast(message, type = 'success') {
    // Creates a styled animated div, auto-removes in 3.5 seconds
    // Does NOT block the JS event loop — spectrogram keeps animating
    const colors = {
        success: 'background: linear-gradient(135deg, #059669, #10b981);',
        error:   'background: linear-gradient(135deg, #dc2626, #ef4444);',
        info:    'background: linear-gradient(135deg, #1d4ed8, #3b82f6);'
    };
    // ... (see main.js for full implementation)
}

// AFTER — All 3 alert() calls replaced
showToast('Data ingested successfully! ✅');         // was: alert(...)
showToast(res.error, 'error');                       // was: alert(res.error)
showToast('Model training complete! 🎯');            // was: alert(...)

// AFTER — .catch() added to ALL fetch() chains
fetch('/api/spectrogram')
    .then(r => r.json())
    .then(res => { /* draw */ })
    .catch(err => console.error('[Spectrogram] Fetch failed:', err));  // <-- added
```

**Lines changed:** Full file rewritten — same logic preserved, improvements layered on top.
Added `showToast()` function (~35 lines), replaced 3 `alert()` calls, added 5 `.catch()` handlers.

---

### 3. `requirements.txt` — New File

**Status:** Created (did not exist before)

```
flask>=2.3.0
werkzeug>=2.3.0
```

**Why this matters:** Without this file, anyone cloning the repo had to manually
read `app.py` imports and guess what to install. Now it's a single command:
`pip install -r requirements.txt`

---

### 4. `README.md` — New File

**Status:** Created (did not exist before)

A comprehensive production-grade README covering:
- Project description & ethical disclaimer
- Features table
- Architecture diagram + data flow
- Tech stack table
- Full installation guide (5 steps)
- Usage guide per page
- API reference table
- Research background with academic citations
- Roadmap

---

## Summary Table

| File | Status | Lines Changed | Impact |
|------|--------|---------------|--------|
| `app.py` | Modified | ~15 added | Eliminates 2 crash vectors; proper HTTP status codes |
| `static/js/main.js` | Modified | ~45 added | No more frozen UI; silent failures now surfaced |
| `requirements.txt` | **New** | 2 lines | One-command install for all contributors |
| `README.md` | **New** | 279 lines | Full project documentation |

**Core EM signal processing, ML architecture, and all HTML/CSS: untouched.**

---

## Why These Changes Matter

| Issue | Before | After |
|-------|--------|-------|
| Visit unknown URL | Flask debug traceback (info leak) | Clean `{"error": "..."}` + 404 |
| Upload with no file | `KeyError` → 500 crash | `{"error": "..."}` + 400 |
| Upload success | Browser `alert()` freezes page | Animated toast, page keeps running |
| Training complete | Browser `alert()` freezes spectrogram | Toast notification, animation unaffected |
| Network failure | Silent — animation dies, no feedback | `.catch()` logs error + shows toast |
| New contributor setup | Read `app.py` and guess dependencies | `pip install -r requirements.txt` |
