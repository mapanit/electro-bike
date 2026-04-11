#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Проверка здоровья сервисов electro-bike..."
echo ""

# Функция для проверки
check_service() {
    local name=$1
    local url=$2
    local expected_code=$3
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_code" ] || [ "$response" -lt 500 ]; then
        echo -e "${GREEN}✓${NC} $name (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗${NC} $name (HTTP $response)"
        return 1
    fi
}

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗${NC} docker-compose не найден"
    exit 1
fi

echo -e "${YELLOW}Контейнеры:${NC}"
docker-compose ps

echo ""
echo -e "${YELLOW}Сервисы:${NC}"

# Ждем немного, чтобы сервисы успели запуститься
sleep 2

# Проверяем сервисы
check_service "Frontend (Next.js)" "http://localhost:3030" "200"
check_service "Backend (Flask)" "http://localhost:8030" "404"

echo ""
echo -e "${YELLOW}База данных:${NC}"
if docker-compose exec -T db mysqladmin ping -h localhost -u root -proot &>/dev/null; then
    echo -e "${GREEN}✓${NC} MySQL база данных"
else
    echo -e "${RED}✗${NC} MySQL база данных"
fi

echo ""
echo "✅ Проверка завершена!"

# Рекомендации
echo ""
echo "📌 Полезные команды:"
echo "   docker-compose logs -f         # Просмотр логов"
echo "   docker-compose logs -f backend # Логи backend"
echo "   docker-compose ps              # Статус сервисов"
echo "   docker-compose down            # Остановка сервисов"
