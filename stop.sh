#!/bin/bash
# MADERA MCP - Stop Script

echo "🛑 Arrêt de MADERA MCP..."
echo ""

docker-compose down

echo ""
echo "✅ Tous les services arrêtés"
echo ""
echo "💡 Pour redémarrer: ./start.sh"
echo "⚠️  Pour supprimer les données: docker-compose down -v"
echo ""
