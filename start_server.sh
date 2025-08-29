#!/bin/bash

# Скрипт для запуска сервера week-planner в фоновом режиме

echo "🚀 Запускаю сервер week-planner..."

# Проверяем, не запущен ли уже сервер
if lsof -i :8000 >/dev/null 2>&1; then
    echo "⚠️  Сервер уже запущен на порту 8000"
    echo "   PID: $(lsof -ti :8000)"
    echo "   URL: http://localhost:8000"
    echo "   Query Analyzer: http://localhost:8000/query-analyzer"
    exit 0
fi

# Запускаем сервер в фоне
echo "📡 Запускаю сервер на порту 8000..."
nohup python3 -m apps.api > server.log 2>&1 &

# Ждем запуска
echo "⏳ Ждем запуска сервера..."
sleep 5

# Проверяем статус
if lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ Сервер успешно запущен!"
    echo "   PID: $(lsof -ti :8000)"
    echo "   URL: http://localhost:8000"
    echo "   Query Analyzer: http://localhost:8000/query-analyzer"
    echo "   Логи: tail -f server.log"
else
    echo "❌ Ошибка запуска сервера"
    echo "   Проверьте логи: cat server.log"
    exit 1
fi
