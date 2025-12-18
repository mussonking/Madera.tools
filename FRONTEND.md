## 🎨 MADERA MCP - FRONTEND DE TRAINING (PHASE 3)

Guide complet pour terminer l'interface web de training avec **Fabric.js** drag-and-drop.

---

## ✅ DÉJÀ COMPLÉTÉ

### Backend (100%)
- ✅ **FastAPI App** ([madera/web/app.py](madera/web/app.py))
- ✅ **Routes Dashboard** ([madera/web/routes/dashboard.py](madera/web/routes/dashboard.py))
- ✅ **Routes Training** ([madera/web/routes/training.py](madera/web/routes/training.py))
- ✅ **Routes API** ([madera/web/routes/api.py](madera/web/routes/api.py))
- ✅ **AI Bot** ([madera/training/bot.py](madera/training/bot.py))
- ✅ **Gemini Agent** ([madera/training/agents/gemini_agent.py](madera/training/agents/gemini_agent.py))

### Structure
```
madera/web/
├── app.py              ✅ FastAPI application
├── routes/
│   ├── __init__.py     ✅
│   ├── dashboard.py    ✅ Dashboard + stats
│   ├── training.py     ✅ Upload + analyse + validation
│   └── api.py          ✅ REST API
├── templates/          🚧 À créer
│   ├── base.html
│   ├── dashboard.html
│   ├── tools.html
│   ├── templates.html
│   └── training/
│       ├── upload.html
│       └── validate.html
└── static/             🚧 À créer
    ├── css/
    │   └── style.css
    └── js/
        ├── app.js
        ├── upload.js
        └── validate.js (Fabric.js)
```

---

## 🚧 À COMPLÉTER

### 1. BASE TEMPLATE (templates/base.html)

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}MADERA Training{% endblock %}</title>

    <!-- CSS -->
    <link rel="stylesheet" href="/static/css/style.css">

    <!-- Fabric.js (pour validation canvas) -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.0/fabric.min.js"></script>

    <!-- Axios (pour AJAX) -->
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>

    {% block extra_head %}{% endblock %}
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="container">
            <a href="/" class="logo">🤖 MADERA Training</a>
            <ul class="nav-links">
                <li><a href="/dashboard">Dashboard</a></li>
                <li><a href="/training">Training</a></li>
                <li><a href="/tools">Tools</a></li>
                <li><a href="/templates">Templates</a></li>
                <li><a href="/api/docs" target="_blank">API Docs</a></li>
            </ul>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="container">
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer>
        <p>MADERA MCP Training UI v0.1.0 | Powered by Gemini Pro</p>
    </footer>

    <!-- Scripts -->
    <script src="/static/js/app.js"></script>
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

---

### 2. DASHBOARD (templates/dashboard.html)

```html
{% extends "base.html" %}

{% block content %}
<h1>📊 Dashboard</h1>

<div class="stats-grid">
    <div class="stat-card">
        <h3>{{ stats.total_executions }}</h3>
        <p>Total Executions</p>
    </div>

    <div class="stat-card">
        <h3>{{ stats.success_rate }}%</h3>
        <p>Success Rate</p>
    </div>

    <div class="stat-card">
        <h3>{{ stats.avg_confidence }}</h3>
        <p>Avg Confidence</p>
    </div>

    <div class="stat-card">
        <h3>{{ stats.avg_execution_time }}ms</h3>
        <p>Avg Time</p>
    </div>

    <div class="stat-card">
        <h3>{{ stats.total_templates }}</h3>
        <p>Templates</p>
    </div>

    <div class="stat-card">
        <h3>{{ stats.pending_queue }}</h3>
        <p>Pending Queue</p>
    </div>
</div>

<div class="actions">
    <a href="/training" class="btn btn-primary">🚀 Start Training</a>
    <a href="/tools" class="btn btn-secondary">🔧 View Tools</a>
</div>
{% endblock %}
```

---

### 3. UPLOAD PAGE (templates/training/upload.html)

```html
{% extends "base.html" %}

{% block content %}
<h1>📤 Upload PDFs for Training</h1>

<div class="upload-section">
    <form id="upload-form" enctype="multipart/form-data">
        <!-- Mode Selection -->
        <div class="form-group">
            <label>Training Mode:</label>
            <select name="mode" id="mode-select">
                <option value="logo_detection">Logo Detection</option>
                <option value="zone_extraction">Zone Extraction</option>
            </select>
        </div>

        <!-- Document Type (optional) -->
        <div class="form-group">
            <label>Document Type (optional):</label>
            <select name="document_type" id="doc-type">
                <option value="">Auto-detect</option>
                <option value="permis_conduire">Permis de conduire</option>
                <option value="carte_assurance_maladie">Carte assurance maladie</option>
                <option value="avis_cotisation">Avis de cotisation</option>
                <option value="t4">T4</option>
                <option value="releve_bancaire">Relevé bancaire</option>
            </select>
        </div>

        <!-- File Upload (Drag & Drop) -->
        <div id="drop-zone" class="drop-zone">
            <p>📂 Drag & drop PDFs here</p>
            <p class="small">or click to browse (max 50 files)</p>
            <input type="file" id="file-input" name="files" multiple accept=".pdf" hidden>
        </div>

        <!-- File List -->
        <div id="file-list" class="file-list" style="display: none;">
            <h3>Files selected: <span id="file-count">0</span></h3>
            <ul id="files"></ul>
        </div>

        <!-- Actions -->
        <div class="form-actions">
            <button type="button" id="analyze-btn" class="btn btn-primary" disabled>
                🤖 Analyze with AI
            </button>
            <button type="button" id="clear-btn" class="btn btn-secondary">
                🗑️ Clear
            </button>
        </div>
    </form>

    <!-- Progress -->
    <div id="progress-section" style="display: none;">
        <h3>⏳ Analyzing...</h3>
        <div class="progress-bar">
            <div id="progress-fill" class="progress-fill"></div>
        </div>
        <p id="progress-text">0 / 0</p>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script src="/static/js/upload.js"></script>
{% endblock %}
```

---

### 4. VALIDATION PAGE avec Fabric.js (templates/training/validate.html)

**C'EST LA PAGE CLÉE - Interface visuelle avec drag-and-drop!**

```html
{% extends "base.html" %}

{% block content %}
<h1>✅ Validate Training Results</h1>

<div class="validation-interface">
    <!-- Left Panel: PDF Preview -->
    <div class="preview-panel">
        <div class="preview-header">
            <h3>Document <span id="current-doc">1</span> / <span id="total-docs">{{ total_files }}</span></h3>
            <p id="doc-filename">document.pdf</p>
        </div>

        <!-- Canvas for Fabric.js -->
        <div class="canvas-container">
            <canvas id="pdf-canvas"></canvas>
        </div>

        <!-- Navigation -->
        <div class="preview-nav">
            <button id="prev-btn" class="btn">⬅️ Previous</button>
            <button id="next-btn" class="btn">Next ➡️</button>
        </div>
    </div>

    <!-- Right Panel: Detection Results -->
    <div class="results-panel">
        <h3>🎯 Detected Elements</h3>

        <!-- Logo Detection Results -->
        <div id="logo-results" style="display: none;">
            <div class="result-item">
                <h4>🏢 <span id="logo-name">SAAQ</span></h4>
                <p>Type: <span id="doc-type">permis_conduire</span></p>
                <p>Confidence: <span id="confidence">94%</span></p>

                <!-- Zone Coordinates (editable) -->
                <div class="zone-editor">
                    <h5>Zone Coordinates:</h5>
                    <label>X: <input type="number" id="zone-x" value="50"></label>
                    <label>Y: <input type="number" id="zone-y" value="30"></label>
                    <label>Width: <input type="number" id="zone-width" value="200"></label>
                    <label>Height: <input type="number" id="zone-height" value="80"></label>
                </div>

                <!-- Actions -->
                <div class="result-actions">
                    <button class="btn btn-success" id="approve-btn">✅ Approve</button>
                    <button class="btn btn-warning" id="edit-btn">✏️ Edit</button>
                    <button class="btn btn-danger" id="reject-btn">❌ Reject</button>
                </div>
            </div>
        </div>

        <!-- AI Suggestions -->
        <div class="suggestions">
            <h4>💡 AI Suggestions:</h4>
            <ul id="suggestions-list">
                <li>Logo detected with high confidence</li>
                <li>Zone coordinates verified</li>
            </ul>
        </div>
    </div>
</div>

<!-- Progress Indicator -->
<div class="validation-progress">
    <div class="progress-bar">
        <div id="val-progress-fill" class="progress-fill"></div>
    </div>
    <p><span id="validated-count">0</span> / {{ total_files }} validated</p>
</div>
{% endblock %}

{% block extra_scripts %}
<script src="/static/js/validate.js"></script>
{% endblock %}
```

---

### 5. FRONTEND JS - Upload (static/js/upload.js)

```javascript
// MADERA MCP - Upload Page Logic

let selectedFiles = [];
let sessionId = null;

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const clearBtn = document.getElementById('clear-btn');

    // Drag & Drop
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');

        const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'));
        handleFiles(files);
    });

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        handleFiles(files);
    });

    // Handle Files
    function handleFiles(files) {
        if (files.length > 50) {
            alert('Maximum 50 files allowed');
            return;
        }

        selectedFiles = files;
        displayFileList();
        analyzeBtn.disabled = files.length === 0;
    }

    function displayFileList() {
        const fileList = document.getElementById('file-list');
        const filesUl = document.getElementById('files');
        const fileCount = document.getElementById('file-count');

        fileCount.textContent = selectedFiles.length;
        filesUl.innerHTML = '';

        selectedFiles.forEach(file => {
            const li = document.createElement('li');
            li.textContent = `📄 ${file.name} (${(file.size / 1024).toFixed(0)} KB)`;
            filesUl.appendChild(li);
        });

        fileList.style.display = 'block';
    }

    // Analyze Button
    analyzeBtn.addEventListener('click', async () => {
        const mode = document.getElementById('mode-select').value;
        const docType = document.getElementById('doc-type').value;

        // Upload files
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('mode', mode);
        if (docType) formData.append('document_type', docType);

        try {
            // Show progress
            document.getElementById('progress-section').style.display = 'block';
            analyzeBtn.disabled = true;

            // Upload
            const uploadResponse = await axios.post('/training/upload', formData, {
                headers: {'Content-Type': 'multipart/form-data'}
            });

            sessionId = uploadResponse.data.session_id;

            // Analyze
            const analyzeFormData = new FormData();
            analyzeFormData.append('mode', mode);
            if (docType) analyzeFormData.append('document_type', docType);

            const analyzeResponse = await axios.post(
                `/training/analyze/${sessionId}`,
                analyzeFormData
            );

            // Redirect to validation
            window.location.href = `/training/validate/${sessionId}`;

        } catch (error) {
            alert('Error: ' + (error.response?.data?.detail || error.message));
            analyzeBtn.disabled = false;
        }
    });

    // Clear Button
    clearBtn.addEventListener('click', () => {
        selectedFiles = [];
        fileInput.value = '';
        document.getElementById('file-list').style.display = 'none';
        analyzeBtn.disabled = true;
    });
});
```

---

### 6. FRONTEND JS - Validation avec Fabric.js (static/js/validate.js)

**COEUR DU SYSTÈME - Drag-and-drop avec Fabric.js!**

```javascript
// MADERA MCP - Validation Page with Fabric.js

let canvas = null;
let currentDoc = 0;
let totalDocs = 0;
let sessionId = null;
let results = [];
let validatedCount = 0;

document.addEventListener('DOMContentLoaded', async () => {
    // Get session ID from URL
    sessionId = window.location.pathname.split('/').pop();

    // Initialize Fabric.js canvas
    canvas = new fabric.Canvas('pdf-canvas', {
        width: 800,
        height: 1000,
        backgroundColor: '#f5f5f5'
    });

    // Load session results
    await loadResults();

    // Display first document
    displayDocument(0);

    // Setup controls
    document.getElementById('prev-btn').addEventListener('click', () => {
        if (currentDoc > 0) {
            displayDocument(currentDoc - 1);
        }
    });

    document.getElementById('next-btn').addEventListener('click', () => {
        if (currentDoc < totalDocs - 1) {
            displayDocument(currentDoc + 1);
        }
    });

    document.getElementById('approve-btn').addEventListener('click', () => {
        approveDetection();
    });

    document.getElementById('edit-btn').addEventListener('click', () => {
        enableZoneEditing();
    });

    document.getElementById('reject-btn').addEventListener('click', () => {
        rejectDetection();
    });
});

async function loadResults() {
    try {
        // Load analysis results from session
        const response = await axios.get(`/api/sessions/${sessionId}/results`);
        results = response.data.results;
        totalDocs = results.length;

        document.getElementById('total-docs').textContent = totalDocs;

    } catch (error) {
        console.error('Failed to load results:', error);
    }
}

function displayDocument(index) {
    currentDoc = index;
    const result = results[index];

    // Update UI
    document.getElementById('current-doc').textContent = index + 1;
    document.getElementById('doc-filename').textContent = result.original_name;

    // Clear canvas
    canvas.clear();

    // Load PDF page as image
    loadPDFImage(result.file_id, (img) => {
        // Add image to canvas
        const fabricImg = new fabric.Image(img, {
            selectable: false,
            evented: false
        });

        // Scale to fit canvas
        const scale = Math.min(
            canvas.width / fabricImg.width,
            canvas.height / fabricImg.height
        );

        fabricImg.scale(scale);
        canvas.add(fabricImg);

        // Draw detected zones
        if (result.analysis && result.analysis.logos_detected) {
            result.analysis.logos_detected.forEach(logo => {
                drawZone(logo.zone, logo.logo_name);
            });
        }

        canvas.renderAll();
    });

    // Update detection info
    if (result.analysis && result.analysis.logos_detected && result.analysis.logos_detected.length > 0) {
        const logo = result.analysis.logos_detected[0];
        document.getElementById('logo-name').textContent = logo.logo_name;
        document.getElementById('doc-type').textContent = logo.document_type;
        document.getElementById('confidence').textContent = (logo.confidence * 100).toFixed(0) + '%';

        // Update zone inputs
        document.getElementById('zone-x').value = logo.zone.x;
        document.getElementById('zone-y').value = logo.zone.y;
        document.getElementById('zone-width').value = logo.zone.width;
        document.getElementById('zone-height').value = logo.zone.height;

        document.getElementById('logo-results').style.display = 'block';
    }

    // Update suggestions
    if (result.analysis && result.analysis.suggestions) {
        const suggestionsList = document.getElementById('suggestions-list');
        suggestionsList.innerHTML = '';
        result.analysis.suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.textContent = suggestion;
            suggestionsList.appendChild(li);
        });
    }
}

function drawZone(zone, label) {
    // Draw rectangle with Fabric.js
    const rect = new fabric.Rect({
        left: zone.x,
        top: zone.y,
        width: zone.width,
        height: zone.height,
        fill: 'rgba(0, 255, 0, 0.2)',
        stroke: '#00ff00',
        strokeWidth: 3,
        selectable: true,  // Allow drag to adjust
        hasControls: true,  // Allow resize
    });

    canvas.add(rect);

    // Add label
    const text = new fabric.Text(label, {
        left: zone.x,
        top: zone.y - 25,
        fontSize: 16,
        fill: '#00ff00',
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        selectable: false
    });

    canvas.add(text);

    // Update inputs when zone is moved/resized
    rect.on('modified', () => {
        document.getElementById('zone-x').value = Math.round(rect.left);
        document.getElementById('zone-y').value = Math.round(rect.top);
        document.getElementById('zone-width').value = Math.round(rect.width * rect.scaleX);
        document.getElementById('zone-height').value = Math.round(rect.height * rect.scaleY);
    });
}

function loadPDFImage(fileId, callback) {
    // Load PDF page as image
    const img = new Image();
    img.onload = () => callback(img);
    img.src = `/api/sessions/${sessionId}/preview/${fileId}`;
}

async function approveDetection() {
    const result = results[currentDoc];

    // Get zone from inputs
    const zone = {
        x: parseInt(document.getElementById('zone-x').value),
        y: parseInt(document.getElementById('zone-y').value),
        width: parseInt(document.getElementById('zone-width').value),
        height: parseInt(document.getElementById('zone-height').value)
    };

    const validatedData = {
        tool_name: 'logo_detector',
        document_type: document.getElementById('doc-type').textContent,
        logo_name: document.getElementById('logo-name').textContent,
        zones: { recto: zone },
        confidence: parseFloat(document.getElementById('confidence').textContent) / 100,
        thresholds: { min_confidence: 0.75 }
    };

    try {
        const formData = new FormData();
        formData.append('file_id', result.file_id);
        formData.append('validated_data', JSON.stringify(validatedData));

        await axios.post(`/training/validate/${sessionId}`, formData);

        // Mark as validated
        validatedCount++;
        updateProgress();

        // Move to next
        if (currentDoc < totalDocs - 1) {
            displayDocument(currentDoc + 1);
        } else {
            // All done!
            alert('🎉 All documents validated!');
            window.location.href = '/dashboard';
        }

    } catch (error) {
        alert('Error saving: ' + error.message);
    }
}

function enableZoneEditing() {
    // Make zones editable (already handled by Fabric.js)
    alert('✏️ Drag or resize the green box to adjust zone coordinates');
}

function rejectDetection() {
    // Skip this document
    if (currentDoc < totalDocs - 1) {
        displayDocument(currentDoc + 1);
    } else {
        alert('End of session');
    }
}

function updateProgress() {
    document.getElementById('validated-count').textContent = validatedCount;
    const percent = (validatedCount / totalDocs) * 100;
    document.getElementById('val-progress-fill').style.width = percent + '%';
}
```

---

### 7. CSS (static/css/style.css)

```css
/* MADERA MCP - Training UI Styles */

:root {
    --primary: #00a67e;
    --secondary: #6c757d;
    --success: #28a745;
    --danger: #dc3545;
    --warning: #ffc107;
    --dark: #212529;
    --light: #f8f9fa;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #f5f5f5;
    color: var(--dark);
}

/* Navbar */
.navbar {
    background: var(--dark);
    color: white;
    padding: 1rem 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.navbar .container {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: white;
    text-decoration: none;
}

.nav-links {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-links a {
    color: white;
    text-decoration: none;
    transition: color 0.3s;
}

.nav-links a:hover {
    color: var(--primary);
}

/* Container */
.container {
    max-width: 1400px;
    margin: 2rem auto;
    padding: 0 2rem;
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.stat-card {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    text-align: center;
}

.stat-card h3 {
    font-size: 2.5rem;
    color: var(--primary);
    margin-bottom: 0.5rem;
}

/* Buttons */
.btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    text-decoration: none;
    display: inline-block;
    transition: all 0.3s;
}

.btn-primary {
    background: var(--primary);
    color: white;
}

.btn-primary:hover {
    background: #008f6e;
}

.btn-secondary {
    background: var(--secondary);
    color: white;
}

.btn-success {
    background: var(--success);
    color: white;
}

.btn-warning {
    background: var(--warning);
    color: white;
}

.btn-danger {
    background: var(--danger);
    color: white;
}

/* Drop Zone */
.drop-zone {
    border: 3px dashed #ccc;
    border-radius: 8px;
    padding: 3rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
}

.drop-zone:hover,
.drop-zone.drag-over {
    border-color: var(--primary);
    background: rgba(0, 166, 126, 0.05);
}

/* Validation Interface */
.validation-interface {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 2rem;
}

.preview-panel,
.results-panel {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.canvas-container {
    margin: 1rem 0;
    border: 2px solid #ddd;
    border-radius: 4px;
    overflow: hidden;
}

/* Progress Bar */
.progress-bar {
    width: 100%;
    height: 30px;
    background: #e9ecef;
    border-radius: 15px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: var(--primary);
    transition: width 0.3s;
}

/* Footer */
footer {
    text-align: center;
    padding: 2rem;
    color: #666;
}
```

---

## 🚀 DÉMARRAGE COMPLET

### 1. Démarrage Backend

```bash
cd /home/mad/madera-mcp

# Avec Docker
docker-compose up -d

# Ou directement
uvicorn madera.web.app:app --reload --host 0.0.0.0 --port 8004
```

### 2. Accès UI

- **Dashboard**: http://localhost:8004/dashboard
- **Training**: http://localhost:8004/training
- **API Docs**: http://localhost:8004/api/docs

### 3. Workflow Complet

1. **Upload** → Drag & drop jusqu'à 50 PDFs
2. **Analyze** → AI Bot (Gemini) analyse automatiquement
3. **Validate** → Interface Fabric.js pour corriger les zones
4. **Save** → Templates sauvegardés en DB
5. **Reuse** → MCP tools utilisent les templates appris

---

## 📦 DÉPENDANCES MANQUANTES

Ajouter à `pyproject.toml`:

```toml
dependencies = [
    # ... existing ...
    "jinja2>=3.1.2",
    "python-multipart>=0.0.6",  # For file uploads
    "aiofiles>=23.0.0",         # For async file operations
]
```

---

## 🎯 PRIORITÉS

### Phase 3A (MVP Frontend - 2-3 jours):
1. ✅ Templates HTML de base (base.html, dashboard.html)
2. ✅ Upload page fonctionnelle avec drag-and-drop
3. ✅ Intégration Fabric.js sur validation page
4. ✅ CSS responsive

### Phase 3B (Polish - 1-2 jours):
5. Améliorer UX (animations, feedback)
6. Ajouter keyboard shortcuts
7. Support multi-pages PDF
8. Export/import templates

---

**STATUS:** Backend 100% ✅ | Frontend à compléter 🚧

Continue avec les templates et JS ci-dessus pour finaliser l'UI! 🎨
