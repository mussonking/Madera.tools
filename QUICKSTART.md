# 🚀 MADERA MCP - Guide de Démarrage Rapide

Guide complet pour démarrer MADERA MCP Training UI en **5 minutes**.

---

## 📋 Pré-requis

- **Docker** et **Docker Compose** installés
- **Clé API Gemini** (gratuit sur https://aistudio.google.com/app/apikey)
- Port **8004** disponible (Web UI)

---

## ⚡ Démarrage Express (3 commandes)

```bash
# 1. Créer le fichier .env avec ta clé API
cp .env.example .env
nano .env  # Ajoute ton GEMINI_API_KEY

# 2. Build + Lancer tous les services
docker-compose up -d --build

# 3. Initialiser la base de données
docker-compose exec madera-web alembic upgrade head
```

**C'est tout!** 🎉 Ouvre http://localhost:8004 dans ton navigateur.

---

## 🔧 Configuration Minimale (.env)

**Obligatoire:**
```env
GEMINI_API_KEY=AIza...  # Ta clé API Gemini (gratuit)
```

**Tout le reste est pré-configuré** (PostgreSQL, Redis, MinIO).

---

## 🌐 Accès Web UI

**URL:** http://localhost:8004

**Navigation:**

```
┌─────────────────────────────────────────┐
│  🏠 Dashboard                           │  ← Stats + vue d'ensemble
├─────────────────────────────────────────┤
│  📤 Training → Upload                   │  ← Commencer un training
├─────────────────────────────────────────┤
│  🛠️ Tools                               │  ← Voir les 7 HINTS tools
├─────────────────────────────────────────┤
│  📋 Templates                           │  ← Templates entraînés
└─────────────────────────────────────────┘
```

---

## 🎓 Premier Training (3 étapes)

### Étape 1: Upload des PDFs

1. Va sur **Training → Upload**
2. **Drag & Drop** tes PDFs (max 50)
3. Choisis le **mode**:
   - **Logo Detection**: Détecter logos (ex: SAAQ, CRA, TD Bank)
   - **Zone Extraction**: Extraire zones (ex: NAS, date naissance)
4. Si mode Logo, choisis le **type de document** (ex: permis_conduire)
5. Clique **Analyser avec AI** ➡️ ⏳ 2-3 secondes

### Étape 2: Validation Visuelle

L'AI a analysé et détecté des zones:

```
┌────────────────────────────────────────┐
│ PDF Preview                            │  ← Canvas avec zones vertes
│  ┌──────────────────────────────┐     │
│  │ [IMAGE]                       │     │
│  │  ┌─────────┐ ← Zone détectée │     │
│  │  │ SAAQ    │                  │     │
│  │  └─────────┘                  │     │
│  └──────────────────────────────┘     │
│                                        │
│ Zone Detected: SAAQ                   │
│ Confidence: 94%                        │
│ Coordinates:                           │
│  X: 120  Y: 80  W: 200  H: 150        │
│                                        │
│ [✅ Approve]  [✏️ Edit]  [❌ Skip]    │
└────────────────────────────────────────┘
```

**Actions:**
- **✅ Approve**: Zone parfaite, sauvegarder
- **✏️ Edit**: Ajuster les coordonnées
  - Drag & drop le rectangle vert
  - Ou modifier manuellement X, Y, W, H
- **❌ Skip**: Document pas bon

### Étape 3: Confirmation

Après approbation:
- Template sauvegardé dans PostgreSQL
- Prochaine détection utilisera ce template
- Précision améliorée!

---

## 🎯 Cas d'Utilisation

### 1. Détecter les cartes d'identité (recto/verso)

**Objectif:** Grouper les pages 1-2 d'un permis de conduire

**Workflow:**
```bash
1. Upload un PDF avec permis (2 pages)
2. Mode: Logo Detection
3. Type: permis_conduire
4. AI détecte logo SAAQ sur page 1
5. Approve ✅
6. Prochaine fois: detection automatique à 95%+
```

### 2. Identifier documents CRA

**Objectif:** Différencier Avis de cotisation vs Allocations familiales

**Workflow:**
```bash
1. Upload PDFs CRA (NOA, RC151, etc.)
2. Mode: Logo Detection
3. Type: avis_cotisation
4. AI détecte logo CRA + texte "Notice of Assessment"
5. Approve ✅
```

### 3. Extraire zones (NAS, dates)

**Objectif:** Définir où chercher le NAS sur un T4

**Workflow:**
```bash
1. Upload T4 2024
2. Mode: Zone Extraction
3. Field Type: sin_number
4. AI suggère zone probablement le NAS (haut-droite)
5. Edit si besoin (drag & drop)
6. Approve ✅
7. Prochains T4: extraction NAS automatique
```

---

## 📊 Dashboard Expliqué

### Stats Cards

```
┌─────────────┬─────────────┬─────────────┐
│ 1,234       │ 98.5%       │ 0.92        │
│ Executions  │ Success     │ Confidence  │
└─────────────┴─────────────┴─────────────┘
┌─────────────┬─────────────┬─────────────┐
│ 12          │ 45          │ 250ms       │
│ Templates   │ Queue       │ Avg Time    │
└─────────────┴─────────────┴─────────────┘
```

- **Executions**: Nombre total d'appels aux tools
- **Success Rate**: % de succès (should be >95%)
- **Avg Confidence**: Confiance moyenne (>0.90 = bon)
- **Templates Trained**: Nombre de templates actifs
- **Training Queue**: Résultats à valider (<0.75 confidence)
- **Avg Execution Time**: Temps moyen (should be <300ms)

---

## 🛠️ Les 7 HINTS Tools

**Visibles sur http://localhost:8004/tools**

| # | Tool | But | Temps |
|---|------|-----|-------|
| 1 | **detect_blank_pages** | Skip pages vides | 50ms |
| 2 | **detect_id_card_sides** | Grouper recto/verso | 50ms |
| 3 | **identify_cra_document_type** | NOA vs RC151 | 200ms |
| 4 | **detect_tax_form_type** | T4 vs T5 vs T1 | 100ms |
| 5 | **detect_document_boundaries** | Split multi-docs | 150ms |
| 6 | **detect_fiscal_year** | Extraire année | 80ms |
| 7 | **assess_image_quality** | Blur, DPI, skew | 100ms |

**Total parallèle: ~250-300ms**

---

## 🔍 Debugging

### Vérifier que tout roule

```bash
# Services actifs?
docker-compose ps

# Logs du web UI
docker-compose logs -f madera-web

# Logs de l'AI bot
docker-compose logs -f madera-celery

# Base de données OK?
docker-compose exec postgres-madera psql -U madera_user -d madera_db -c "\dt"
```

### Problèmes courants

**Problème:** "Can't connect to database"
```bash
# Attendre que PostgreSQL soit ready
docker-compose exec postgres-madera pg_isready -U madera_user
# Si pas ready: docker-compose restart postgres-madera
```

**Problème:** "Gemini API error"
```bash
# Vérifier ta clé API
docker-compose exec madera-web env | grep GEMINI
# Si vide: édite .env et restart
docker-compose restart madera-web
```

**Problème:** Page blanche (localhost:8004)
```bash
# Vérifier les logs
docker-compose logs madera-web
# Rebuild si nécessaire
docker-compose up -d --build madera-web
```

---

## 📁 Architecture des Services

```
┌──────────────────────────────────────┐
│  madera-web (port 8004)              │  ← Web UI (FastAPI + Jinja2)
└──────────────────────────────────────┘
           ↓ ↓ ↓
┌──────────────────────────────────────┐
│  postgres-madera (port 5433)         │  ← Base de données
└──────────────────────────────────────┘
┌──────────────────────────────────────┐
│  redis-madera (port 6380)            │  ← Queue Celery
└──────────────────────────────────────┘
┌──────────────────────────────────────┐
│  madera-celery                       │  ← AI workers (async)
└──────────────────────────────────────┘
┌──────────────────────────────────────┐
│  madera-beat                         │  ← Scheduler (cron jobs)
└──────────────────────────────────────┘
```

**Ports:**
- **8004**: Web UI
- **5433**: PostgreSQL (externe)
- **6380**: Redis (externe)
- **8003**: MCP Server (stdio, pas HTTP)

---

## 🔄 Commandes Utiles

### Gestion des services

```bash
# Démarrer tout
docker-compose up -d

# Voir les logs en temps réel
docker-compose logs -f

# Redémarrer un service
docker-compose restart madera-web

# Arrêter tout
docker-compose down

# Supprimer les volumes (⚠️ efface la DB)
docker-compose down -v
```

### Base de données

```bash
# Migrations
docker-compose exec madera-web alembic upgrade head

# Créer une migration
docker-compose exec madera-web alembic revision --autogenerate -m "description"

# Rollback
docker-compose exec madera-web alembic downgrade -1

# Accès PostgreSQL
docker-compose exec postgres-madera psql -U madera_user -d madera_db
```

### Développement

```bash
# Rebuild après changement de code
docker-compose up -d --build

# Hot reload (déjà activé avec --reload)
# Édite madera/web/*.py → reload automatique

# Shell dans le container
docker-compose exec madera-web bash

# Tests
docker-compose exec madera-web pytest tests/
```

---

## 🎨 Personnalisation

### Changer les couleurs (CSS)

Édite [madera/web/static/css/style.css](madera/web/static/css/style.css:5):

```css
:root {
    --primary: #00a67e;        /* Vert MADERA */
    --primary-dark: #008f6e;
    --success: #28a745;        /* Vert succès */
    --danger: #dc3545;         /* Rouge erreur */
}
```

Refresh page → nouvelles couleurs!

### Ajouter un type de document

Édite [madera/web/routes/training.py](madera/web/routes/training.py):

```python
DOCUMENT_TYPES = {
    "permis_conduire": "Permis de conduire",
    "t4": "T4 (Fédéral)",
    "ma_nouvelle_carte": "Ma Nouvelle Carte",  # ← Ajouter ici
}
```

Restart → nouveau type disponible!

---

## 📚 API REST (Optionnel)

**Base URL:** http://localhost:8004/api

### Endpoints

```bash
# Liste des tools
GET /api/tools

# Templates entraînés
GET /api/templates

# Stats
GET /api/stats
```

**Exemple:**
```bash
curl http://localhost:8004/api/tools | jq
```

**Réponse:**
```json
{
  "tools": [
    {
      "name": "detect_blank_pages",
      "description": "Detects blank or near-blank pages...",
      "avg_execution_time": 45.2,
      "success_rate": 0.99
    },
    ...
  ]
}
```

---

## 🚀 Intégration avec LeClasseur

**Prochaine étape** (pas encore implémentée):

```python
# Dans LeClasseur backend
from madera_client import MaderaClient

client = MaderaClient()
hints = await client.get_hints(presigned_url)

# Enrichir prompt Gemini avec hints
enriched_prompt = f"""
{base_prompt}

HINTS:
- ID Cards: {hints['id_cards']}
- Blank pages: {hints['blank_pages']}
- Fiscal year: {hints['fiscal_years']}
"""

result = await analyze_with_gemini(enriched_prompt, images)
```

**Gains attendus:**
- ✅ **-60% tokens** (skip pages blanches)
- ✅ **+40% précision** (contexte)
- ✅ **-30% temps total** (hints rapides)

---

## 📞 Support

**Problème non résolu?**

1. Check logs: `docker-compose logs -f`
2. Vérifier .env: `docker-compose exec madera-web env | grep -E "(DATABASE|GEMINI)"`
3. Rebuild: `docker-compose up -d --build`
4. Clean start: `docker-compose down -v && docker-compose up -d --build`

---

## 🎯 Checklist de Démarrage

- [ ] Docker et Docker Compose installés
- [ ] `.env` créé avec `GEMINI_API_KEY`
- [ ] `docker-compose up -d --build` exécuté
- [ ] `alembic upgrade head` exécuté
- [ ] http://localhost:8004 accessible
- [ ] Dashboard affiche stats (même si zéro)
- [ ] Premier training complété

**Tout vert?** 🎉 Tu es prêt à entraîner MADERA!

---

## 📖 Documentation Complète

- **Architecture Plan**: [plan.md](.claude/plans/majestic-noodling-hopcroft.md)
- **Frontend Guide**: [FRONTEND.md](FRONTEND.md)
- **Testing Guide**: [TESTING.md](TESTING.md)
- **API Reference**: http://localhost:8004/docs (Swagger)

---

**Made with ❤️ by Mad** | MADERA Tools v0.1.0
