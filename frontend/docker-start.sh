#!/bin/sh
echo "🚀 Démarrage JurisRoute Frontend (SQLite)..."

# Créer le fichier SQLite si absent
mkdir -p database
touch database/database.sqlite

# Fix permissions — les volumes Windows sont montés en root, PHP-FPM tourne en www-data
chown -R www-data:www-data database storage bootstrap/cache
chmod -R 775 database storage bootstrap/cache
chmod 664 database/database.sqlite

# Générer la clé
php artisan key:generate --no-interaction 2>/dev/null || true

# Migrations SQLite
php artisan migrate --force --no-interaction

# Caches
php artisan config:cache
php artisan route:cache
php artisan view:cache

echo "✅ Laravel + SQLite prêt !"

php-fpm -D
nginx -g "daemon off;"