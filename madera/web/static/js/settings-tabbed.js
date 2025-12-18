/**
 * MADERA Settings - Tabbed Interface
 * Manages training configuration for all 4 modes
 */

let logos = [];
let categories = [];
let docTypes = [];

document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeAIModelForm();
    loadLogos();
    loadCategories();
    loadDocTypes();
});

// ========== TAB MANAGEMENT ==========

function initializeTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;

            // Update buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === tabId) {
                    content.classList.add('active');
                }
            });
        });
    });
}

// ========== AI MODELS TAB ==========

function initializeAIModelForm() {
    // Provider change
    document.querySelectorAll('input[name="provider"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const provider = e.target.value;

            document.querySelectorAll('.provider-card').forEach(card => {
                card.classList.remove('active');
            });
            e.target.closest('.provider-card').classList.add('active');

            document.querySelectorAll('.models-list').forEach(list => {
                list.style.display = list.dataset.provider === provider ? 'block' : 'none';
            });

            const firstModel = document.querySelector(`.models-list[data-provider="${provider}"] input[type="radio"]`);
            if (firstModel) {
                firstModel.checked = true;
                document.getElementById('customModel').value = firstModel.value;
            }
        });
    });

    // Model preset change
    document.querySelectorAll('input[name="model_preset"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            document.getElementById('customModel').value = e.target.value;
        });
    });

    // Custom model input
    document.getElementById('customModel').addEventListener('input', () => {
        document.querySelectorAll('input[name="model_preset"]').forEach(radio => {
            radio.checked = false;
        });
    });

    // Form submit
    document.getElementById('settingsForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const provider = document.querySelector('input[name="provider"]:checked').value;
        const modelName = document.getElementById('customModel').value.trim();

        if (!modelName) {
            showMessage('Please enter a model name', 'error');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('provider', provider);
            formData.append('model_name', modelName);

            const response = await fetch('/settings/api/update', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                showMessage(`✓ ${data.message}`, 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showMessage(`✗ ${data.error}`, 'error');
            }
        } catch (error) {
            showMessage(`✗ Failed: ${error.message}`, 'error');
        }
    });
}

// ========== LOGO DETECTION TAB ==========

async function loadLogos() {
    try {
        const response = await fetch('/settings/api/logos');
        const data = await response.json();
        logos = data.logos || [];
        renderLogosTable();
    } catch (error) {
        console.error('Failed to load logos:', error);
    }
}

function renderLogosTable() {
    const tbody = document.getElementById('logosTableBody');
    if (!tbody) return;

    if (logos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #666;">No logos defined</td></tr>';
        return;
    }

    tbody.innerHTML = logos.map(logo => `
        <tr>
            <td><code>${logo.code}</code></td>
            <td>${logo.display}</td>
            <td><span class="badge">${logo.category}</span></td>
            <td>
                <button class="btn-delete" onclick="deleteLogo('${logo.code}')">🗑️</button>
            </td>
        </tr>
    `).join('');
}

// Add logo form
document.addEventListener('DOMContentLoaded', () => {
    const addLogoForm = document.getElementById('addLogoForm');
    if (addLogoForm) {
        addLogoForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const code = document.getElementById('logoCode').value.trim();
            const display = document.getElementById('logoDisplay').value.trim();
            const category = document.getElementById('logoCategory').value;

            if (!code || !display || !category) {
                showMessage('Please fill all fields', 'error');
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
                    showMessage('✓ Logo added', 'success');
                    logos = data.logos;
                    renderLogosTable();
                    addLogoForm.reset();
                } else {
                    showMessage(`✗ ${data.error}`, 'error');
                }
            } catch (error) {
                showMessage(`✗ Failed: ${error.message}`, 'error');
            }
        });
    }
});

async function deleteLogo(code) {
    if (!confirm(`Delete logo "${code}"?`)) return;

    try {
        const response = await fetch(`/settings/api/logos/${code}`, { method: 'DELETE' });
        const data = await response.json();

        if (data.success) {
            showMessage('✓ Logo deleted', 'success');
            logos = data.logos;
            renderLogosTable();
        } else {
            showMessage('✗ Failed to delete', 'error');
        }
    } catch (error) {
        showMessage(`✗ Error: ${error.message}`, 'error');
    }
}

// ========== CATEGORIES MANAGEMENT ==========

async function loadCategories() {
    try {
        const response = await fetch('/settings/api/categories');
        const data = await response.json();
        categories = data.categories || [];
        renderCategoryList();
        updateCategoryDropdowns();
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

function renderCategoryList() {
    const container = document.getElementById('categoryList');
    if (!container) return;

    if (categories.length === 0) {
        container.innerHTML = '<p style="color: #666;">No custom categories defined</p>';
        return;
    }

    container.innerHTML = categories.map(cat => `
        <div class="category-badge">
            <span style="font-size: 20px;">${cat.icon}</span>
            <span><strong>${cat.label}</strong><br><code>${cat.code}</code></span>
            <button class="btn-delete" onclick="deleteCategory('${cat.code}')" style="margin-left: auto;">×</button>
        </div>
    `).join('');
}

function updateCategoryDropdowns() {
    const logoCategory = document.getElementById('logoCategory');
    if (!logoCategory) return;

    // Keep default options, add custom ones
    const defaultOptions = logoCategory.innerHTML;
    const customOptions = categories.map(cat =>
        `<option value="${cat.code}">${cat.icon} ${cat.label}</option>`
    ).join('');

    logoCategory.innerHTML = defaultOptions + customOptions;
}

document.addEventListener('DOMContentLoaded', () => {
    const addCategoryForm = document.getElementById('addCategoryForm');
    if (addCategoryForm) {
        addCategoryForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const code = document.getElementById('categoryCode').value.trim().toLowerCase();
            const label = document.getElementById('categoryLabel').value.trim();
            const icon = document.getElementById('categoryIcon').value.trim();

            try {
                const formData = new FormData();
                formData.append('code', code);
                formData.append('label', label);
                formData.append('icon', icon);

                const response = await fetch('/settings/api/categories/add', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    showMessage('✓ Category added', 'success');
                    categories = data.categories;
                    renderCategoryList();
                    updateCategoryDropdowns();
                    addCategoryForm.reset();
                } else {
                    showMessage(`✗ ${data.error}`, 'error');
                }
            } catch (error) {
                showMessage(`✗ Failed: ${error.message}`, 'error');
            }
        });
    }
});

async function deleteCategory(code) {
    if (!confirm(`Delete category "${code}"?`)) return;

    try {
        const response = await fetch(`/settings/api/categories/${code}`, { method: 'DELETE' });
        const data = await response.json();

        if (data.success) {
            showMessage('✓ Category deleted', 'success');
            categories = data.categories;
            renderCategoryList();
            updateCategoryDropdowns();
        }
    } catch (error) {
        showMessage(`✗ Error: ${error.message}`, 'error');
    }
}

// ========== DOCUMENT TYPES TAB ==========

async function loadDocTypes() {
    try {
        const response = await fetch('/settings/api/doctypes');
        const data = await response.json();
        docTypes = data.doctypes || [];
        renderDocTypesTable();
    } catch (error) {
        console.error('Failed to load doc types:', error);
    }
}

function renderDocTypesTable() {
    const tbody = document.getElementById('docTypesTableBody');
    if (!tbody) return;

    if (docTypes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #666;">No document types defined</td></tr>';
        return;
    }

    tbody.innerHTML = docTypes.map(dt => `
        <tr>
            <td><code>${dt.code}</code></td>
            <td>${dt.label}</td>
            <td><span class="badge">${dt.category}</span></td>
            <td>
                <button class="btn-delete" onclick="deleteDocType('${dt.code}')">🗑️</button>
            </td>
        </tr>
    `).join('');
}

document.addEventListener('DOMContentLoaded', () => {
    const addDocTypeForm = document.getElementById('addDocTypeForm');
    if (addDocTypeForm) {
        addDocTypeForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const code = document.getElementById('docTypeCode').value.trim();
            const label = document.getElementById('docTypeLabel').value.trim();
            const category = document.getElementById('docTypeCategory').value;

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
                    showMessage('✓ Document type added', 'success');
                    docTypes = data.doctypes;
                    renderDocTypesTable();
                    addDocTypeForm.reset();
                } else {
                    showMessage(`✗ ${data.error}`, 'error');
                }
            } catch (error) {
                showMessage(`✗ Failed: ${error.message}`, 'error');
            }
        });
    }
});

async function deleteDocType(code) {
    if (!confirm(`Delete document type "${code}"?`)) return;

    try {
        const response = await fetch(`/settings/api/doctypes/${code}`, { method: 'DELETE' });
        const data = await response.json();

        if (data.success) {
            showMessage('✓ Document type deleted', 'success');
            docTypes = data.doctypes;
            renderDocTypesTable();
        }
    } catch (error) {
        showMessage(`✗ Error: ${error.message}`, 'error');
    }
}

// ========== UTILITY FUNCTIONS ==========

function showMessage(text, type) {
    const msg = document.getElementById('statusMessage');
    if (!msg) return;

    msg.textContent = text;
    msg.className = `status-message ${type}`;
    msg.style.display = 'block';

    setTimeout(() => {
        msg.style.display = 'none';
    }, 5000);
}

console.log('✅ Settings tabbed interface loaded');
