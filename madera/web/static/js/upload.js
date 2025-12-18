/**
 * MADERA Training - Upload Page
 * Handles drag & drop, file selection, and AI analysis
 */

let selectedFiles = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeDragDrop();
    initializeFileInput();
    initializeModeSelection();
});

// Fix: Ensure mode selection persists
function initializeModeSelection() {
    const modeCards = document.querySelectorAll('.mode-card');

    modeCards.forEach(card => {
        card.addEventListener('click', (e) => {
            // Ensure the radio gets checked
            const radio = card.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                console.log('Mode selected:', radio.value);

                // Visual feedback
                modeCards.forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
            }
        });
    });

    // Set initial selected state
    const checkedRadio = document.querySelector('input[name="mode"]:checked');
    if (checkedRadio) {
        const checkedCard = checkedRadio.closest('.mode-card');
        if (checkedCard) {
            checkedCard.classList.add('selected');
        }
    }
}

// Drag & Drop functionality
function initializeDragDrop() {
    const uploadBox = document.getElementById('uploadBox');
    if (!uploadBox) return;

    uploadBox.addEventListener('click', () => {
        document.getElementById('fileInput').click();
    });

    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('dragover');
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('dragover');
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('dragover');

        const files = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
        handleFiles(files);
    });
}

// File Input
function initializeFileInput() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput) return;

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        handleFiles(files);
    });
}

function handleFiles(files) {
    // Limit to 50 files
    if (selectedFiles.length + files.length > 50) {
        alert('Maximum 50 fichiers autorisés!');
        return;
    }

    selectedFiles = [...selectedFiles, ...files];
    renderFiles();

    // Enable start button
    const startBtn = document.getElementById('startBtn');
    if (startBtn) {
        startBtn.disabled = selectedFiles.length === 0;
    }
}

function renderFiles() {
    const filesGrid = document.getElementById('filesGrid');
    const filesList = document.getElementById('filesList');
    const fileCount = document.getElementById('fileCount');

    if (!filesGrid || !filesList || !fileCount) return;

    if (selectedFiles.length === 0) {
        filesList.style.display = 'none';
        return;
    }

    filesList.style.display = 'block';
    fileCount.textContent = selectedFiles.length;

    filesGrid.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <button class="file-remove" onclick="removeFile(${index})">×</button>
            <div class="file-icon">📄</div>
            <div class="file-name">${file.name}</div>
            <div class="file-size">${formatBytes(file.size)}</div>
        </div>
    `).join('');
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderFiles();

    const startBtn = document.getElementById('startBtn');
    if (startBtn) {
        startBtn.disabled = selectedFiles.length === 0;
    }
}

function clearFiles() {
    selectedFiles = [];
    renderFiles();

    const startBtn = document.getElementById('startBtn');
    if (startBtn) {
        startBtn.disabled = true;
    }

    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.value = '';
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

async function startAnalysis() {
    if (selectedFiles.length === 0) {
        alert('Veuillez sélectionner des fichiers!');
        return;
    }

    const modeInput = document.querySelector('input[name="mode"]:checked');
    if (!modeInput) {
        alert('Veuillez sélectionner un mode de training!');
        return;
    }
    const mode = modeInput.value;

    const progressSection = document.getElementById('analysisProgress');
    const startBtn = document.getElementById('startBtn');

    if (progressSection) progressSection.style.display = 'block';
    if (startBtn) startBtn.disabled = true;

    const formData = new FormData();
    selectedFiles.forEach((file) => {
        formData.append('files', file);
    });
    formData.append('mode', mode);

    try {
        updateProgress(0, 'Uploading files...');

        const response = await fetch('/training/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            await analyzeWithAI(data.session_id);
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('Erreur upload: ' + error.message);

        if (progressSection) progressSection.style.display = 'none';
        if (startBtn) startBtn.disabled = false;
    }
}

async function analyzeWithAI(sessionId) {
    updateProgress(50, 'AI Analysis in progress with Gemini...');

    try {
        const response = await fetch(`/training/analyze/${sessionId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            updateProgress(100, 'Analysis complete! Redirecting...');

            setTimeout(() => {
                window.location.href = `/training/validate/${sessionId}`;
            }, 1000);
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
    } catch (error) {
        console.error('Analysis error:', error);
        alert('Erreur analyse: ' + error.message);

        const progressSection = document.getElementById('analysisProgress');
        const startBtn = document.getElementById('startBtn');

        if (progressSection) progressSection.style.display = 'none';
        if (startBtn) startBtn.disabled = false;
    }
}

function updateProgress(percent, text) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    if (progressFill) {
        progressFill.style.width = percent + '%';
        progressFill.textContent = percent + '%';
    }

    if (progressText) {
        progressText.textContent = text;
    }
}
