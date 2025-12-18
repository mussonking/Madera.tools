#!/bin/bash
# MADERA MCP - Quick Start Script
# Made with ❤️ by Mad

set -e

echo "🚀 MADERA MCP - Démarrage Rapide"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Fichier .env manquant!"
    echo "➡️  Copie de .env.example vers .env..."
    cp .env.example .env
    echo "✅ Fichier .env créé"
    echo ""
    echo "⚠️  IMPORTANT: Édite .env et ajoute ta GEMINI_API_KEY"
    echo "    Obtiens-la gratuitement sur: https://aistudio.google.com/app/apikey"
    echo ""
    read -p "Appuie sur Entrée quand c'est fait..."
fi

# Check if GEMINI_API_KEY is set
if ! grep -q "GEMINI_API_KEY=AIza" .env 2>/dev/null && ! grep -q "GEMINI_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  GEMINI_API_KEY semble vide dans .env"
    echo "    Le training AI ne fonctionnera pas sans clé API"
    echo ""
    read -p "Continuer quand même? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🐋 Démarrage Docker Compose..."
echo ""

# Build and start services
docker-compose up -d --build

echo ""
echo "⏳ Attente que les services soient prêts..."
sleep 5

# Wait for PostgreSQL
echo "   Vérification PostgreSQL..."
until docker-compose exec -T postgres-madera pg_isready -U madera_user -d madera_db > /dev/null 2>&1; do
    echo "   PostgreSQL pas encore prêt, attente..."
    sleep 2
done
echo "   ✅ PostgreSQL prêt"

# Wait for Redis
echo "   Vérification Redis..."
until docker-compose exec -T redis-madera redis-cli ping > /dev/null 2>&1; do
    echo "   Redis pas encore prêt, attente..."
    sleep 2
done
echo "   ✅ Redis prêt"

# Run migrations
echo ""
echo "🔄 Initialisation de la base de données..."
docker-compose exec -T madera-web alembic upgrade head

echo ""
echo "✅ MADERA MCP est prêt!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Web UI:       http://localhost:8004"
echo "📊 Dashboard:    http://localhost:8004/dashboard"
echo "📤 Upload:       http://localhost:8004/training/upload"
echo "🛠️  Tools:        http://localhost:8004/tools"
echo "📋 Templates:    http://localhost:8004/templates"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Commandes utiles:"
echo "   docker-compose logs -f           # Voir les logs"
echo "   docker-compose logs -f madera-web # Logs Web UI"
echo "   docker-compose restart madera-web # Redémarrer Web UI"
echo "   docker-compose down              # Arrêter tout"
echo ""
echo "🎓 Guide complet: QUICKSTART.md"
echo ""
