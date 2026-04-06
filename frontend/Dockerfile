# Build stage
FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Build para produção
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Instala servidor estático simples
RUN npm install -g serve

# Copia build do stage anterior
COPY --from=builder /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
