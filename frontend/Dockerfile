FROM php:8.4-fpm-alpine
WORKDIR /var/www/html

# Extensions PHP + SQLite
RUN apk add --no-cache \
    nginx \
    nodejs \
    npm \
    git \
    curl \
    sqlite \
    sqlite-dev \
    libpng-dev \
    zip \
    unzip \
    oniguruma-dev \
    && docker-php-ext-install pdo pdo_sqlite gd mbstring

# Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

COPY . .

RUN composer install --no-dev --optimize-autoloader --no-interaction

RUN npm install && npm run build 2>/dev/null || true

# Créer le fichier SQLite s'il n'existe pas
RUN mkdir -p database && touch database/database.sqlite

RUN chown -R www-data:www-data storage bootstrap/cache database \
    && chmod -R 775 storage bootstrap/cache database

# Config Nginx
RUN printf 'server {\n\
    listen 80;\n\
    root /var/www/html/public;\n\
    index index.php;\n\
    location / {\n\
        try_files $uri $uri/ /index.php?$query_string;\n\
    }\n\
    location ~ \\.php$ {\n\
        fastcgi_pass 127.0.0.1:9000;\n\
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;\n\
        include fastcgi_params;\n\
    }\n\
    client_max_body_size 20M;\n\
}\n' > /etc/nginx/http.d/default.conf

COPY docker-start.sh /docker-start.sh
RUN sed -i 's/\r$//' /docker-start.sh && chmod +x /docker-start.sh

EXPOSE 80
CMD ["/docker-start.sh"]