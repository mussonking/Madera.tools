/**
 * MADERA MCP - Tools Page JavaScript
 * Dynamic loading, filtering, search, and modal functionality
 */

// State
let allTools = [];
let categories = [];
let currentCategory = 'all';
let currentSubcategory = 'all';
let searchQuery = '';

// DOM Elements
const toolsGrid = document.getElementById('tools-grid');
const categoryTabs = document.querySelector('.category-tabs');
const subcategoryPills = document.getElementById('subcategory-pills');
const searchInput = document.getElementById('tool-search');
const modal = document.getElementById('toolModal');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    loadTools();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Search
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase();
        renderTools();
    });

    // Close modal on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeToolModal();
        }
    });

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeToolModal();
        }
    });
}

// Load categories from API
async function loadCategories() {
    try {
        const response = await axios.get('/api/categories');
        categories = response.data.categories;

        // Update stats
        const stats = response.data.stats;
        document.getElementById('total-tools').textContent = stats.total_tools;

        if (stats.categories.pdf) {
            document.getElementById('pdf-tools').textContent = stats.categories.pdf.total_tools;
        }
        if (stats.categories.debug) {
            document.getElementById('debug-tools').textContent = stats.categories.debug.total_tools;
        }

        renderCategoryTabs();
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Load tools from API
async function loadTools() {
    try {
        const response = await axios.get('/api/tools');
        allTools = response.data.tools;
        renderTools();
    } catch (error) {
        console.error('Failed to load tools:', error);
        toolsGrid.innerHTML = `
            <div class="no-results">
                <h3>Failed to load tools</h3>
                <p>Please try refreshing the page.</p>
            </div>
        `;
    }
}

// Render category tabs
function renderCategoryTabs() {
    // Keep "All" tab, add category tabs
    let tabsHtml = `
        <button class="category-tab ${currentCategory === 'all' ? 'active' : ''}"
                data-category="all" onclick="selectCategory('all')">
            <span class="tab-icon">*</span>
            <span class="tab-name">All Tools</span>
        </button>
    `;

    categories.forEach(cat => {
        tabsHtml += `
            <button class="category-tab ${currentCategory === cat.id ? 'active' : ''}"
                    data-category="${cat.id}" onclick="selectCategory('${cat.id}')">
                <span class="tab-icon">${cat.icon}</span>
                <span class="tab-name">${cat.name}</span>
            </button>
        `;
    });

    categoryTabs.innerHTML = tabsHtml;
    renderSubcategoryPills();
}

// Render subcategory pills
function renderSubcategoryPills() {
    if (currentCategory === 'all') {
        // Show all subcategories from all categories
        let pillsHtml = `
            <button class="subcat-pill ${currentSubcategory === 'all' ? 'active' : ''}"
                    onclick="selectSubcategory('all')"
                    style="--subcat-color: #667eea; --subcat-bg: rgba(102, 126, 234, 0.1);">
                <span class="pill-icon">*</span>
                <span>All</span>
            </button>
        `;

        categories.forEach(cat => {
            cat.subcategories.forEach(subcat => {
                const count = allTools.filter(t => t.subcategory === subcat.id).length;
                pillsHtml += `
                    <button class="subcat-pill ${currentSubcategory === subcat.id ? 'active' : ''}"
                            onclick="selectSubcategory('${subcat.id}')"
                            style="--subcat-color: ${subcat.color}; --subcat-bg: ${subcat.color}15;">
                        <span class="pill-icon">${subcat.icon}</span>
                        <span>${subcat.name}</span>
                        <span class="pill-count">${count}</span>
                    </button>
                `;
            });
        });

        subcategoryPills.innerHTML = pillsHtml;
    } else {
        // Show subcategories for selected category
        const category = categories.find(c => c.id === currentCategory);
        if (!category) return;

        let pillsHtml = `
            <button class="subcat-pill ${currentSubcategory === 'all' ? 'active' : ''}"
                    onclick="selectSubcategory('all')"
                    style="--subcat-color: ${category.color}; --subcat-bg: ${category.color}15;">
                <span class="pill-icon">*</span>
                <span>All ${category.name}</span>
            </button>
        `;

        category.subcategories.forEach(subcat => {
            const count = allTools.filter(t => t.subcategory === subcat.id).length;
            pillsHtml += `
                <button class="subcat-pill ${currentSubcategory === subcat.id ? 'active' : ''}"
                        onclick="selectSubcategory('${subcat.id}')"
                        style="--subcat-color: ${subcat.color}; --subcat-bg: ${subcat.color}15;">
                    <span class="pill-icon">${subcat.icon}</span>
                    <span>${subcat.name}</span>
                    <span class="pill-count">${count}</span>
                </button>
            `;
        });

        subcategoryPills.innerHTML = pillsHtml;
    }
}

// Select category
function selectCategory(categoryId) {
    currentCategory = categoryId;
    currentSubcategory = 'all'; // Reset subcategory when category changes
    renderCategoryTabs();
    renderTools();
}

// Select subcategory
function selectSubcategory(subcategoryId) {
    currentSubcategory = subcategoryId;
    renderSubcategoryPills();
    renderTools();
}

// Filter tools based on current filters and search
function getFilteredTools() {
    return allTools.filter(tool => {
        // Category filter
        if (currentCategory !== 'all' && tool.category !== currentCategory) {
            return false;
        }

        // Subcategory filter
        if (currentSubcategory !== 'all' && tool.subcategory !== currentSubcategory) {
            return false;
        }

        // Search filter
        if (searchQuery) {
            const searchLower = searchQuery.toLowerCase();
            const matchName = tool.name.toLowerCase().includes(searchLower);
            const matchDesc = (tool.short_description || '').toLowerCase().includes(searchLower);
            const matchFullDesc = (tool.description || '').toLowerCase().includes(searchLower);
            if (!matchName && !matchDesc && !matchFullDesc) {
                return false;
            }
        }

        return true;
    });
}

// Render tools grid
function renderTools() {
    const filteredTools = getFilteredTools();

    if (filteredTools.length === 0) {
        toolsGrid.innerHTML = `
            <div class="no-results">
                <h3>No tools found</h3>
                <p>Try adjusting your filters or search query.</p>
            </div>
        `;
        return;
    }

    // Group by subcategory for better organization
    const grouped = {};
    filteredTools.forEach(tool => {
        const subcat = tool.subcategory || 'unknown';
        if (!grouped[subcat]) {
            grouped[subcat] = [];
        }
        grouped[subcat].push(tool);
    });

    let html = '';
    filteredTools.forEach(tool => {
        const catInfo = tool.category_info || {};
        const color = catInfo.color || '#667eea';
        const bgColor = color + '15'; // 15% opacity

        html += `
            <div class="tool-card"
                 onclick="openToolModal('${tool.name}')"
                 style="--card-color: ${color}; --card-bg: ${bgColor};">
                <div class="tool-card-header">
                    <span class="tool-card-icon">${catInfo.subcategory_icon || '?'}</span>
                    <h3>${tool.name}</h3>
                </div>
                <p class="description">${tool.short_description || 'No description'}</p>
                <div class="meta">
                    <span class="subcat-tag">${catInfo.subcategory_name || 'Unknown'}</span>
                    <span class="details-link">Details &rarr;</span>
                </div>
            </div>
        `;
    });

    toolsGrid.innerHTML = html;
}

// Open tool modal with details
async function openToolModal(toolName) {
    try {
        const response = await axios.get(`/api/tools/${toolName}`);
        const tool = response.data;
        const catInfo = tool.category_info || {};

        // Populate modal
        document.getElementById('modal-icon').textContent = catInfo.subcategory_icon || '?';
        document.getElementById('modal-tool-name').textContent = tool.name;
        document.getElementById('modal-description').textContent = tool.description || 'No description available.';

        // Category badges
        const catBadge = document.getElementById('modal-category');
        catBadge.textContent = `${catInfo.category_icon || ''} ${catInfo.category_name || 'Unknown'}`;
        catBadge.style.background = (catInfo.color || '#667eea') + '20';
        catBadge.style.color = catInfo.color || '#667eea';

        const subcatBadge = document.getElementById('modal-subcategory');
        subcatBadge.textContent = `${catInfo.subcategory_icon || ''} ${catInfo.subcategory_name || 'Unknown'}`;
        subcatBadge.style.background = (catInfo.color || '#10b981') + '20';
        subcatBadge.style.color = catInfo.color || '#10b981';

        // Arguments
        const argsContainer = document.getElementById('modal-args');
        const schema = tool.input_schema || {};
        const properties = schema.properties || {};
        const required = schema.required || [];

        if (Object.keys(properties).length === 0) {
            argsContainer.innerHTML = '<div class="no-args">No arguments required</div>';
        } else {
            let argsHtml = '';
            Object.entries(properties).forEach(([name, prop]) => {
                const isRequired = required.includes(name);
                argsHtml += `
                    <div class="arg-row">
                        <span class="arg-name">${name}${isRequired ? ' *' : ''}</span>
                        <span class="arg-type">${prop.type || 'any'}</span>
                        <span class="arg-desc">${prop.description || '-'}</span>
                    </div>
                `;
            });
            argsContainer.innerHTML = argsHtml;
        }

        // Returns (example output structure)
        const returnsBlock = document.getElementById('modal-returns');
        returnsBlock.textContent = JSON.stringify({
            success: true,
            data: '...',
            hints: '...',
            confidence: 0.95,
            execution_time_ms: 100
        }, null, 2);

        // Stats
        const stats = tool.stats || {};
        document.getElementById('modal-executions').textContent = stats.total_executions || 0;
        document.getElementById('modal-success-rate').textContent =
            (stats.success_rate || 0).toFixed(1) + '%';
        document.getElementById('modal-avg-time').textContent =
            (stats.avg_execution_time_ms || 0).toFixed(0) + 'ms';

        // Show modal
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';

    } catch (error) {
        console.error('Failed to load tool details:', error);
        alert('Failed to load tool details. Please try again.');
    }
}

// Close tool modal
function closeToolModal() {
    modal.classList.remove('active');
    document.body.style.overflow = '';
}
