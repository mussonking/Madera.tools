# MADERA MCP - TODO TESTING
## Documents de test pour améliorer les 40 tools

---

## 📋 PHASE 1: HINTS TOOLS (7 tools)

### Documents à tester:

- [ ] **detect_blank_pages**
  - PDF avec pages blanches intercalées
  - PDF scanné avec pages presque vides
  - PDF avec pages de séparation

- [ ] **detect_id_card_sides**
  - Permis de conduire QC (recto + verso)
  - Carte d'assurance maladie QC (recto + verso)
  - Passeport canadien
  - Carte de crédit (tester si détecte correctement)

- [ ] **identify_cra_document_type**
  - Avis de cotisation CRA (NOA)
  - Allocations familiales (RC151)
  - Crédit TPS/TVH
  - Option C / Proof of income
  - Statement of Account

- [ ] **detect_tax_form_type**
  - T4 (plusieurs années)
  - T4A, T4E, T5
  - T1 General
  - RL-1 (Québec)
  - RL-2 (Québec)

- [ ] **detect_document_boundaries**
  - PDF multi-documents (3-4 docs fusionnés)
  - PDF avec pages blanches séparatrices
  - PDF avec changements de header/footer

- [ ] **detect_fiscal_year**
  - Documents fiscaux 2022, 2023, 2024
  - Documents avec années mixtes
  - Documents sans année claire

- [ ] **assess_image_quality**
  - PDF scanné haute qualité (300 DPI)
  - PDF scanné basse qualité (150 DPI)
  - PDF flou ou penché
  - PDF trop sombre/trop clair

---

## 📄 PHASE 2: PDF MANIPULATION (5 tools)

### Documents à tester:

- [ ] **count_pages**
  - PDF 1 page
  - PDF 10+ pages
  - PDF 50+ pages

- [ ] **extract_page**
  - Extraire page 1, 5, dernière page
  - Tester avec PDF de tailles variées

- [ ] **split_pdf**
  - Split "1-3,5,7-9"
  - Split "1-10" puis "11-20"
  - Split avec ranges invalides (test erreur)

- [ ] **merge_pdfs**
  - Merger 2 PDFs
  - Merger 5+ PDFs
  - Tester avec PDFs de formats différents

- [ ] **rotate_page**
  - Rotation 90°, 180°, 270°
  - Rotation de page déjà tournée
  - Rotation multiple pages

---

## 📝 PHASE 2: TEXT EXTRACTION (4 tools)

### Documents à tester:

- [ ] **extract_text**
  - PDF texte natif (Word → PDF)
  - PDF scanné (image-based) → devrait retourner vide
  - PDF mixte (texte + images)

- [ ] **extract_text_by_page**
  - PDF multi-pages avec texte variable
  - Vérifier que chaque page est bien séparée

- [ ] **search_text**
  - Chercher téléphone: `\d{3}-\d{3}-\d{4}`
  - Chercher email: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
  - Chercher NAS: `\d{3}[ -]?\d{3}[ -]?\d{3}`
  - Chercher montants: `\$\s?[\d,]+\.?\d*`

- [ ] **extract_tables**
  - PDF avec tableaux simples
  - PDF avec tableaux complexes (colonnes multiples)
  - Statement bancaire avec transactions

---

## 🔢 PHASE 2: NORMALIZATION (6 tools)

### Données à tester:

- [ ] **normalize_address**
  - "123 rue de l'Église, Montréal, QC"
  - "123 Rue Eglise Montreal"
  - "123 RUE DE L'EGLISE MONTREAL"
  - Adresses avec accents, tirets, virgules

- [ ] **parse_currency**
  - "$15,000.50"
  - "15 000,50 $" (format canadien français)
  - "(1,234.56)" (négatif comptable)
  - "15000.5", "15000"

- [ ] **parse_date**
  - "15 janvier 2025"
  - "2025-01-15"
  - "01/15/2025" vs "15/01/2025"
  - "January 15, 2025"

- [ ] **normalize_name**
  - "Jean-François Tremblay"
  - "MARIE-PIERRE O'BRIEN"
  - "josé garcía"

- [ ] **split_full_name**
  - "Jean Tremblay"
  - "Jean-François Marie Tremblay"
  - "O'Brien"
  - "Smith Jr."

- [ ] **calculate_address_similarity**
  - "123 Rue de l'Église, Montreal" vs "123 rue Eglise Montreal"
  - Adresses similaires mais pas identiques
  - Adresses complètement différentes

---

## 💰 PHASE 3: FINANCIAL CALCULATIONS (5 tools)

### Scénarios à tester:

- [ ] **calculate_annual_income**
  - Biweekly: $2,500 → $65,000
  - Monthly: $5,000 → $60,000
  - Weekly: $1,200 → $62,400
  - Semi-monthly: $2,400 → $57,600

- [ ] **calculate_gds_tds**
  - Revenu: $80,000
  - Hypothèque: $2,000/mois
  - Taxes: $300/mois
  - Chauffage: $100/mois
  - Condo: $200/mois
  - Autres dettes: $500/mois
  - **Vérifier si GDS < 39% et TDS < 44%**

- [ ] **calculate_ltv**
  - Propriété: $500,000, Prêt: $450,000 → 90% LTV
  - Propriété: $500,000, Prêt: $400,000 → 80% LTV
  - Propriété: $500,000, Prêt: $475,000 → 95% LTV
  - **Vérifier calcul assurance SCHL**

- [ ] **average_t4_income**
  - T4 2022: $65,000
  - T4 2023: $70,000
  - T4 2024: $72,000
  - **Vérifier moyenne et trend (increasing/decreasing)**

- [ ] **estimate_monthly_payment**
  - Prêt: $400,000
  - Taux: 5.25%
  - Amortissement: 25 ans
  - **Vérifier formule canadienne (semi-annuel compounding)**

---

## ✅ PHASE 3: DATA VALIDATION (5 tools)

### Données à tester:

- [ ] **validate_sin**
  - Valide: "123 456 782"
  - Invalide: "000 000 000"
  - Invalide: "800 000 000" (commence par 8)
  - Format: "123-456-782", "123456782"

- [ ] **validate_postal_code**
  - Canadien valide: "K1A 0B1", "H3Z 2Y7"
  - Canadien invalide: "K0A 0B1" (second char = 0)
  - US valide: "12345", "12345-6789"
  - US invalide: "1234", "123456"

- [ ] **validate_phone**
  - Valide: "514-555-1234", "(514) 555-1234"
  - Valide avec +1: "+1-514-555-1234"
  - Invalide: "011-555-1234" (area code commence par 0/1)
  - Invalide: "514-055-1234" (exchange commence par 0/1)

- [ ] **validate_email**
  - Valide: "john.doe@example.com"
  - Valide: "John.Doe@Example.COM" (normalise à lowercase)
  - Invalide: "john@", "john@.com", "@example.com"

- [ ] **validate_date_range**
  - Valide: "2024-01-01" à "2024-12-31"
  - Invalide: "2024-12-31" à "2024-01-01" (end < start)
  - Max 365 jours: tester avec max_days=365

---

## 🚀 PHASE 3: ADVANCED TOOLS (8 tools)

### Documents à tester:

- [ ] **generate_thumbnail**
  - PDF 1 page → thumbnail 300px
  - PDF multi-pages → thumbnail page 5
  - Tester sizes: 150px, 300px, 600px

- [ ] **detect_bank_statement_type**
  - Statement TD
  - Statement RBC
  - Statement Desjardins
  - Statement banque inconnue

- [ ] **detect_form_fields**
  - PDF formulaire fillable (avec champs)
  - PDF formulaire non-fillable (image)
  - PDF avec signatures

- [ ] **count_signatures**
  - PDF avec 3 champs signature
  - PDF avec signatures remplies vs vides
  - PDF sans signatures

- [ ] **extract_urls**
  - PDF avec liens cliquables
  - PDF avec URLs dans le texte
  - PDF sans URLs

- [ ] **compress_pdf**
  - PDF lourd (5+ MB) → compression high
  - PDF moyen (1 MB) → compression medium
  - PDF léger (100 KB) → compression low

- [ ] **pdf_to_images**
  - PDF 3 pages → 3 PNGs à 200 DPI
  - PDF 10 pages → 5 PNGs max (test max_pages)
  - Tester DPI: 150, 200, 300

- [ ] **images_to_pdf**
  - 3 PNGs → 1 PDF
  - Images RGBA → RGB conversion
  - Images différentes tailles

---

## 🎯 PRIORITÉS DE TEST

### Urgent (tester en premier):
1. **HINTS tools** - Impact direct sur réduction tokens AI
2. **Financial calculations** - Dossiers hypothécaires
3. **Validation tools** - Qualité des données

### Moyen:
4. **Text extraction** - Alternative à vision AI
5. **Normalization** - Matching addresses/names

### Nice to have:
6. **PDF manipulation** - Moins critique
7. **Advanced tools** - Features bonus

---

## 📊 MÉTRIQUES À TRACKER

Pour chaque tool testé, noter:

- ✅ **Precision**: % de bonnes détections
- ⏱️ **Speed**: Temps d'exécution moyen
- 🐛 **Bugs**: Erreurs trouvées
- 💡 **Improvements**: Idées d'amélioration

---

## 🔧 AMÉLIORER LES TOOLS APRÈS TESTS

### Templates à entraîner (après tests):

1. **Logo detection** (detect_bank_statement_type)
   - Ajouter logos manquants
   - Améliorer zones de détection

2. **Pattern matching** (identify_cra_document_type, detect_tax_form_type)
   - Ajouter patterns manquants
   - Ajuster seuils de confiance

3. **OCR zones** (detect_fiscal_year)
   - Optimiser zones de scan
   - Ajuster DPI si flou

---

## 📁 ORGANISATION DES TESTS

Créer dossier: `/home/mad/madera-mcp/test-documents/`

```
test-documents/
├── hints/
│   ├── blank-pages/
│   ├── id-cards/
│   ├── cra-docs/
│   ├── tax-forms/
│   └── quality/
├── pdf-manipulation/
├── text-extraction/
├── normalization/ (fichier .txt avec test cases)
├── financial/ (fichier .txt avec test cases)
├── validation/ (fichier .txt avec test cases)
└── advanced/
    ├── bank-statements/
    ├── forms/
    └── images/
```

---

## ✅ CHECKLIST RAPIDE

- [ ] Uploader 5-10 documents par catégorie
- [ ] Tester via Web UI http://192.168.2.71:8004/tools
- [ ] Tester via API POST http://192.168.2.71:8004/api/tools/{tool_name}
- [ ] Noter precision/bugs dans un fichier
- [ ] Ajuster thresholds dans les tools si besoin
- [ ] Ajouter templates/patterns manquants

---

**STATUS**: 40/40 tools prêts à tester 🚀
