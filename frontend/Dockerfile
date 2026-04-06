# Build stage
FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build para produção
RUN npm run build

# Production stage - Use nginx para servir os arquivos estáticos
FROM nginx:alpine

# Remove configuração padrão do nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copia arquivos do build
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuração do nginx para servir SPA (React Router)
RUN echo 'server { listen 3000; server_name localhost; location / { root /usr/share/nginx/html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
