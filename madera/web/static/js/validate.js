// MADERA MCP - Validation Page with Fabric.js
// Vanilla JS + Fabric.js for canvas drag-and-drop

let canvas = null;
let currentDoc = 0;
let totalDocs = 0;
let sessionId = null;
let results = [];
let validatedCount = 0;
let currentZoneRect = null;
let logoDatabase = [];
let doctypeDatabase = [];
let categoriesDatabase = [];

document.addEventListener('DOMContentLoaded', async () => {
    // Get session ID from hidden input
    sessionId = document.getElementById('session-id').value;

    if (!sessionId) {
        App.toast('No session ID found', 'error');
        return;
    }

    // Initialize Fabric.js canvas
    canvas = new fabric.Canvas('pdf-canvas', {
        width: 850,
        height: 1100,
        backgroundColor: '#f5f5f5',
        selection: true
    });

    // Load databases for dropdowns
    await loadLogoDatabase();
    await loadDoctypeDatabase();
    await loadCategoriesDatabase();

    // Load session results
    await loadResults();

    // Display first document
    if (results.length > 0) {
        displayDocument(0);
    }

    // Setup controls
    setupControls();
    setupQuickAddModals();
});

function setupControls() {
    // Previous button
    document.getElementById('prev-btn').addEventListener('click', () => {
        if (currentDoc > 0) {
            displayDocument(currentDoc - 1);
        }
    });

    // Next button
    document.getElementById('next-btn').addEventListener('click', () => {
        if (currentDoc < totalDocs - 1) {
            displayDocument(currentDoc + 1);
        } else {
            // All done
            completeValidation();
        }
    });

    // Skip button
    document.getElementById('skip-btn').addEventListener('click', () => {
        // Skip without saving
        if (currentDoc < totalDocs - 1) {
            displayDocument(currentDoc + 1);
        }
    });

    // Approve button
    document.getElementById('approve-btn').addEventListener('click', async () => {
        await approveDetection();
    });

    // Reject button
    document.getElementById('reject-btn').addEventListener('click', () => {
        // Skip this document
        if (currentDoc < totalDocs - 1) {
            displayDocument(currentDoc + 1);
        }
    });

    // Zone input changes
    const zoneInputs = ['zone-x', 'zone-y', 'zone-width', 'zone-height'];
    zoneInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('change', updateZoneFromInputs);
        }
    });
}

async function loadLogoDatabase() {
    try {
        const response = await fetch('/settings/api/logos');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        logoDatabase = data.logos || [];

        // Populate logo dropdown with categories
        const logoSelect = document.getElementById('logo-name');
        logoSelect.innerHTML = '<option value="">Select logo...</option>';

        // Group by category
        const categories = {
            bank: '🏦 Banks',
            government: '🏛️ Government',
            insurance: '🛡️ Insurance',
            credit: '📊 Credit Bureaus'
        };

        // Create optgroups
        Object.keys(categories).forEach(category => {
            const categoryLogos = logoDatabase.filter(logo => logo.category === category);
            if (categoryLogos.length > 0) {
                const optgroup = document.createElement('optgroup');
                optgroup.label = categories[category];

                categoryLogos.forEach(logo => {
                    const option = document.createElement('option');
                    option.value = logo.code;
                    option.textContent = logo.display;
                    optgroup.appendChild(option);
                });

                logoSelect.appendChild(optgroup);
            }
        });

        console.log(`✅ Loaded ${logoDatabase.length} logos`);
    } catch (error) {
        console.error('Failed to load logo database:', error);
    }
}

async function loadResults() {
    try {
        // Fetch actual session results
        const response = await fetch(`/training/api/session/${sessionId}/results`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        results = data.files || [];
        totalDocs = results.length;

        if (totalDocs === 0) {
            console.warn('No documents to validate');
            alert('No documents to validate');
        }

        document.getElementById('total-docs').textContent = totalDocs;

    } catch (error) {
        console.error('Failed to load results:', error);
        alert('Failed to load session results: ' + error.message);
    }
}

function displayDocument(index) {
    if (index < 0 || index >= totalDocs) {
        return;
    }

    currentDoc = index;

    // Update UI
    document.getElementById('current-doc').textContent = index + 1;

    // Clear canvas
    canvas.clear();
    currentZoneRect = null;

    // In production, load actual PDF page as image
    // For now, create placeholder
    loadDocumentImage(index);

    // Update nav buttons
    document.getElementById('prev-btn').disabled = (index === 0);
    document.getElementById('next-btn').disabled = (index === totalDocs - 1);
}

function loadDocumentImage(index) {
    const file = results[index];
    if (!file) return;

    // Update filename
    document.getElementById('doc-filename').textContent = file.original_name;

    // Load PDF page image
    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = () => {
        const fabricImg = new fabric.Image(img, {
            left: 0,
            top: 0,
            selectable: false,
            evented: false
        });

        // Scale to fit canvas
        const scale = Math.min(
            canvas.width / img.width,
            canvas.height / img.height
        );
        fabricImg.scale(scale);

        canvas.add(fabricImg);
        canvas.sendToBack(fabricImg);

        // Draw detected zones from AI analysis
        if (file.analysis && file.analysis.logos_detected) {
            const logos = file.analysis.logos_detected;
            if (logos.length > 0) {
                const logo = logos[0]; // First logo

                // Draw detection zone
                if (logo.bounding_box) {
                    // Convert percentage coordinates to pixels
                    // Gemini returns percentages (0-100), we need pixels
                    const bbox = {
                        x: (logo.bounding_box.x / 100) * img.width * scale,
                        y: (logo.bounding_box.y / 100) * img.height * scale,
                        width: (logo.bounding_box.width / 100) * img.width * scale,
                        height: (logo.bounding_box.height / 100) * img.height * scale
                    };

                    drawDetectionZone(bbox, logo.name);

                    // Update sidebar - use .value for inputs
                    document.getElementById('logo-name').value = logo.name;
                    document.getElementById('doc-type').value = file.analysis.document_type || '-';
                    document.getElementById('confidence').textContent = `${(logo.confidence * 100).toFixed(0)}%`;
                    document.getElementById('zone-x').value = Math.round(bbox.x);
                    document.getElementById('zone-y').value = Math.round(bbox.y);
                    document.getElementById('zone-width').value = Math.round(bbox.width);
                    document.getElementById('zone-height').value = Math.round(bbox.height);
                }
            }
        }

        // Update AI suggestions
        updateSuggestions(file.analysis);

        canvas.renderAll();
    };

    img.onerror = () => {
        console.error('Failed to load image:', file.image_url);
        // Show placeholder
        const text = new fabric.Text(`Failed to load image`, {
            left: canvas.width / 2,
            top: canvas.height / 2,
            fontSize: 24,
            fill: '#e53e3e',
            originX: 'center',
            originY: 'center',
            selectable: false
        });
        canvas.add(text);
        canvas.renderAll();
    };

    img.src = file.image_url;
}

function drawDetectionZone(zone, label) {
    // Remove existing zone if any
    if (currentZoneRect) {
        canvas.remove(currentZoneRect);
    }

    // Draw rectangle with Fabric.js
    currentZoneRect = new fabric.Rect({
        left: zone.x,
        top: zone.y,
        width: zone.width,
        height: zone.height,
        fill: 'rgba(0, 255, 0, 0.2)',
        stroke: '#00ff00',
        strokeWidth: 3,
        selectable: true,  // Allow drag to adjust
        hasControls: true,  // Allow resize
        lockRotation: true  // Prevent rotation
    });

    canvas.add(currentZoneRect);

    // Add label above zone
    const labelText = new fabric.Text(label, {
        left: zone.x,
        top: zone.y - 30,
        fontSize: 18,
        fill: '#ffffff',
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        padding: 5,
        selectable: false
    });

    canvas.add(labelText);

    // Update inputs when zone is moved/resized
    currentZoneRect.on('modified', () => {
        updateInputsFromZone();
    });

    currentZoneRect.on('moving', () => {
        updateInputsFromZone();
    });

    currentZoneRect.on('scaling', () => {
        updateInputsFromZone();
    });

    canvas.renderAll();
}

function updateInputsFromZone() {
    if (!currentZoneRect) return;

    document.getElementById('zone-x').value = Math.round(currentZoneRect.left);
    document.getElementById('zone-y').value = Math.round(currentZoneRect.top);
    document.getElementById('zone-width').value = Math.round(currentZoneRect.width * currentZoneRect.scaleX);
    document.getElementById('zone-height').value = Math.round(currentZoneRect.height * currentZoneRect.scaleY);
}

function updateZoneFromInputs() {
    if (!currentZoneRect) return;

    const x = parseInt(document.getElementById('zone-x').value);
    const y = parseInt(document.getElementById('zone-y').value);
    const width = parseInt(document.getElementById('zone-width').value);
    const height = parseInt(document.getElementById('zone-height').value);

    currentZoneRect.set({
        left: x,
        top: y,
        width: width / currentZoneRect.scaleX,
        height: height / currentZoneRect.scaleY
    });

    canvas.renderAll();
}

function updateSuggestions(analysis) {
    const suggestionsList = document.getElementById('suggestions-list');

    if (!suggestionsList) return;

    // Clear loading message
    suggestionsList.innerHTML = '';

    if (!analysis) {
        suggestionsList.innerHTML = '<li>No AI analysis available</li>';
        return;
    }

    const suggestions = [];

    // Generate suggestions based on analysis
    if (analysis.logos_detected && analysis.logos_detected.length > 0) {
        const logo = analysis.logos_detected[0];
        suggestions.push(`Detected: <strong>${logo.name}</strong>`);

        if (logo.confidence < 0.8) {
            suggestions.push(`⚠️ Low confidence (${(logo.confidence * 100).toFixed(0)}%) - please verify`);
        } else {
            suggestions.push(`✅ High confidence (${(logo.confidence * 100).toFixed(0)}%)`);
        }

        if (analysis.document_type) {
            suggestions.push(`Document type: ${analysis.document_type}`);
        }
    } else if (analysis.zones && analysis.zones.length > 0) {
        suggestions.push(`Found ${analysis.zones.length} zones`);
        analysis.zones.forEach((zone, i) => {
            suggestions.push(`Zone ${i + 1}: ${zone.label} (${zone.type})`);
        });
    } else {
        suggestions.push('No detections found - manual entry required');
    }

    // Render suggestions
    if (suggestions.length === 0) {
        suggestionsList.innerHTML = '<li>No suggestions available</li>';
    } else {
        suggestionsList.innerHTML = suggestions.map(s => `<li>${s}</li>`).join('');
    }
}

async function approveDetection() {
    // Check if entity should be skipped (non-important)
    const skipEntity = document.getElementById('skip-entity').checked;

    if (skipEntity) {
        // Don't save, just move to next
        console.log('⏭️ Skipping non-important entity');
        if (currentDoc < totalDocs - 1) {
            displayDocument(currentDoc + 1);
        } else {
            completeValidation();
        }
        return;
    }

    // Get zone from inputs
    const zone = {
        x: parseInt(document.getElementById('zone-x').value),
        y: parseInt(document.getElementById('zone-y').value),
        width: parseInt(document.getElementById('zone-width').value),
        height: parseInt(document.getElementById('zone-height').value)
    };

    const validatedData = {
        tool_name: 'logo_detector',
        document_type: document.getElementById('doc-type').value,  // Changed to .value
        logo_name: document.getElementById('logo-name').value,      // Changed to .value
        zones: {
            recto: zone
        },
        confidence: parseFloat(document.getElementById('confidence').textContent.replace('%', '')) / 100,
        thresholds: {
            min_confidence: 0.75
        },
        skip_entity: false  // Explicitly mark as important
    };

    try {
        const formData = new FormData();
        formData.append('file_id', results[currentDoc].file_id);
        formData.append('validated_data', JSON.stringify(validatedData));

        const response = await fetch(`/training/validate/${sessionId}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log('✅ Validation saved!', result);
        alert('✅ Validation saved!');

        // Mark as validated
        validatedCount++;
        updateProgress();

        // Move to next
        if (currentDoc < totalDocs - 1) {
            displayDocument(currentDoc + 1);
        } else {
            completeValidation();
        }

    } catch (error) {
        console.error('Save validation error:', error);
        alert('❌ Save failed: ' + error.message);
    }
}

function updateProgress() {
    document.getElementById('validated-count').textContent = validatedCount;
    const percent = (validatedCount / totalDocs) * 100;
    document.getElementById('val-progress-fill').style.width = percent + '%';
}

function completeValidation() {
    alert('🎉 All documents validated!');

    setTimeout(async () => {
        try {
            // Cleanup session and redirect
            await fetch(`/training/session/${sessionId}`, { method: 'DELETE' });
        } catch (error) {
            console.error('Cleanup error:', error);
        } finally {
            window.location.href = '/dashboard';
        }
    }, 2000);
}

// ========== DOCTYPE DATABASE ==========

async function loadDoctypeDatabase() {
    try {
        const response = await fetch('/settings/api/doctypes');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        doctypeDatabase = data.doctypes || [];

        // Populate doctype dropdown
        const doctypeSelect = document.getElementById('doc-type');
        doctypeSelect.innerHTML = '<option value="">Select type...</option>';

        doctypeDatabase.forEach(dt => {
            const option = document.createElement('option');
            option.value = dt.code;
            option.textContent = dt.label;
            doctypeSelect.appendChild(option);
        });

        console.log(`✅ Loaded ${doctypeDatabase.length} document types`);
    } catch (error) {
        console.error('Failed to load doctype database:', error);
    }
}

// ========== CATEGORIES DATABASE ==========

async function loadCategoriesDatabase() {
    try {
        const response = await fetch('/settings/api/categories');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        categoriesDatabase = data.categories || [];

        // Update logo category dropdown in quick-add modal
        updateLogoModalCategories();

        console.log(`✅ Loaded ${categoriesDatabase.length} custom categories`);
    } catch (error) {
        console.error('Failed to load categories database:', error);
    }
}

function updateLogoModalCategories() {
    const categorySelect = document.getElementById('quick-logo-category');
    if (!categorySelect) return;

    // Keep default options
    const defaultOptions = `
        <option value="">Select category...</option>
        <option value="bank">🏦 Bank</option>
        <option value="government">🏛️ Government</option>
        <option value="insurance">🛡️ Insurance</option>
        <option value="credit">📊 Credit Bureau</option>
    `;

    // Add custom categories
    const customOptions = categoriesDatabase.map(cat =>
        `<option value="${cat.code}">${cat.icon} ${cat.label}</option>`
    ).join('');

    categorySelect.innerHTML = defaultOptions + customOptions;
}

// ========== QUICK ADD MODALS ==========

function setupQuickAddModals() {
    // Add Logo button
    const addLogoBtn = document.getElementById('add-logo-btn');
    if (addLogoBtn) {
        addLogoBtn.addEventListener('click', () => {
            openQuickAddLogoModal();
        });
    }

    // Add Doctype button
    const addDoctypeBtn = document.getElementById('add-doctype-btn');
    if (addDoctypeBtn) {
        addDoctypeBtn.addEventListener('click', () => {
            openQuickAddDoctypeModal();
        });
    }

    // Quick Add Logo Form
    const logoForm = document.getElementById('quickAddLogoForm');
    if (logoForm) {
        logoForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await submitQuickAddLogo();
        });
    }

    // Quick Add Doctype Form
    const doctypeForm = document.getElementById('quickAddDoctypeForm');
    if (doctypeForm) {
        doctypeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await submitQuickAddDoctype();
        });
    }
}

// ========== LOGO QUICK ADD ==========

function openQuickAddLogoModal() {
    const modal = document.getElementById('quickAddLogoModal');
    if (!modal) return;

    // Auto-detect: suggest current value as code
    const currentLogoValue = document.getElementById('logo-name').value;
    if (currentLogoValue && currentLogoValue.trim()) {
        document.getElementById('quick-logo-code').value = currentLogoValue.toUpperCase().replace(/\s+/g, '_');
        document.getElementById('quick-logo-display').value = currentLogoValue;
    }

    modal.style.display = 'flex';
}

function closeQuickAddLogoModal() {
    const modal = document.getElementById('quickAddLogoModal');
    if (modal) {
        modal.style.display = 'none';
        document.getElementById('quickAddLogoForm').reset();
        document.getElementById('quick-logo-message').style.display = 'none';
    }
}

async function submitQuickAddLogo() {
    const code = document.getElementById('quick-logo-code').value.trim();
    const display = document.getElementById('quick-logo-display').value.trim();
    const category = document.getElementById('quick-logo-category').value;

    if (!code || !display || !category) {
        showQuickLogoMessage('Please fill all fields', 'error');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('code', code);
        formData.append('display', display);
        formData.append('category', category);

        const response = await fetch('/settings/api/logos/add', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showQuickLogoMessage('✅ Logo added successfully!', 'success');

            // Reload logo database
            await loadLogoDatabase();

            // Select the new logo
            document.getElementById('logo-name').value = code.toUpperCase().replace(/\s+/g, '_');

            // Close modal after delay
            setTimeout(() => {
                closeQuickAddLogoModal();
            }, 1500);
        } else {
            showQuickLogoMessage(`❌ ${data.error}`, 'error');
        }
    } catch (error) {
        showQuickLogoMessage(`❌ Failed: ${error.message}`, 'error');
    }
}

function showQuickLogoMessage(text, type) {
    const msg = document.getElementById('quick-logo-message');
    if (!msg) return;

    msg.textContent = text;
    msg.className = `status-message ${type}`;
    msg.style.display = 'block';

    setTimeout(() => {
        msg.style.display = 'none';
    }, 5000);
}

// ========== DOCTYPE QUICK ADD ==========

function openQuickAddDoctypeModal() {
    const modal = document.getElementById('quickAddDoctypeModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeQuickAddDoctypeModal() {
    const modal = document.getElementById('quickAddDoctypeModal');
    if (modal) {
        modal.style.display = 'none';
        document.getElementById('quickAddDoctypeForm').reset();
        document.getElementById('quick-doctype-message').style.display = 'none';
    }
}

async function submitQuickAddDoctype() {
    const code = document.getElementById('quick-doctype-code').value.trim();
    const label = document.getElementById('quick-doctype-label').value.trim();
    const category = document.getElementById('quick-doctype-category').value;

    if (!code || !label || !category) {
        showQuickDoctypeMessage('Please fill all fields', 'error');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('code', code);
        formData.append('label', label);
        formData.append('category', category);

        const response = await fetch('/settings/api/doctypes/add', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showQuickDoctypeMessage('✅ Document type added successfully!', 'success');

            // Reload doctype database
            await loadDoctypeDatabase();

            // Select the new doctype
            document.getElementById('doc-type').value = code.toLowerCase().replace(/\s+/g, '_');

            // Close modal after delay
            setTimeout(() => {
                closeQuickAddDoctypeModal();
            }, 1500);
        } else {
            showQuickDoctypeMessage(`❌ ${data.error}`, 'error');
        }
    } catch (error) {
        showQuickDoctypeMessage(`❌ Failed: ${error.message}`, 'error');
    }
}

function showQuickDoctypeMessage(text, type) {
    const msg = document.getElementById('quick-doctype-message');
    if (!msg) return;

    msg.textContent = text;
    msg.className = `status-message ${type}`;
    msg.style.display = 'block';

    setTimeout(() => {
        msg.style.display = 'none';
    }, 5000);
}

console.log('🎯 Validation page ready with Fabric.js');
