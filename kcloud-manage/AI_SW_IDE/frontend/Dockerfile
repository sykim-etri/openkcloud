# 1. Build React app
FROM node:22 AS build
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

# 2. Serve static files using Nginx
FROM nginx:latest

# gettext-base for envsubst command
RUN apt-get update && apt-get install -y gettext-base && rm -rf /var/lib/apt/lists/*

COPY --from=build /app/dist /usr/share/nginx/html
COPY public/config.js.template /usr/share/nginx/html/config.js.template
COPY scripts/inject-env.sh /docker-entrypoint.d/inject-env.sh
RUN chmod +x /docker-entrypoint.d/inject-env.sh

EXPOSE 80
CMD ["/docker-entrypoint.d/inject-env.sh"]