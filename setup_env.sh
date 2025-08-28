#!/bin/bash

# WeekPlanner Wave-2 ENV Setup Script
# Запустите: source setup_env.sh

echo "🚀 Настройка ENV для WeekPlanner Wave-2..."

# Создаем директории
mkdir -p data/snapshots

# БД: локальный SQLite (MVP)
export DB_URL="sqlite:////$PWD/data/wp.db"
echo "✅ DB_URL: $DB_URL"

# Redis: замените на свои данные!
echo "⚠️  ВНИМАНИЕ: Замените REDIS_URL на ваш managed Redis инстанс"
export REDIS_URL="redis://default:G0vadDS1N9IaEoqQLukwSEGdAHUuPiaW@redis-14374.crce194.ap-seast-1-1.ec2.redns.redis-cloud.com:14374"
echo "✅ REDIS_URL: $REDIS_URL"

# Город и кеш-политика
export CITY="bangkok"
export CACHE_TTL_S="1200"           # 20 минут
export CACHE_SWR_MARGIN_S="600"     # +10 минут stale-while-revalidate
echo "✅ CITY: $CITY"
echo "✅ CACHE_TTL_S: $CACHE_TTL_S"
echo "✅ CACHE_SWR_MARGIN_S: $CACHE_SWR_MARGIN_S"

# Снапшоты HTML
export SNAPSHOT_ENABLE="true"
export SNAPSHOT_TOP_PERCENT="0.2"   # топ-20% карточек
export SNAPSHOT_DIR="$PWD/data/snapshots"
echo "✅ SNAPSHOT_ENABLE: $SNAPSHOT_ENABLE"
echo "✅ SNAPSHOT_TOP_PERCENT: $SNAPSHOT_TOP_PERCENT"
echo "✅ SNAPSHOT_DIR: $SNAPSHOT_DIR"

# QA отчет
export QA_JSON_OUT="$PWD/qa_report.json"
echo "✅ QA_JSON_OUT: $QA_JSON_OUT"

# Дополнительные настройки
export FETCH_PAUSE_MS="1000"        # 1 секунда между источниками
export DAYS_AHEAD="7"               # Кэшировать на 7 дней вперед
echo "✅ FETCH_PAUSE_MS: $FETCH_PAUSE_MS"
echo "✅ DAYS_AHEAD: $DAYS_AHEAD"

echo ""
echo "🎯 ENV переменные настроены!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Замените REDIS_URL на ваш managed Redis"
echo "2. Запустите первичную загрузку: python3 scripts/run_ingest.py --once"
echo "3. Проверьте содержимое БД и Redis"
echo ""
echo "💡 Для сохранения ENV в файл: env | grep -E '^(DB_URL|REDIS_URL|CITY|CACHE|SNAPSHOT|QA_JSON|FETCH|DAYS)' > .env"
