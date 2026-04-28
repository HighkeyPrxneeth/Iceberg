# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Set build-time variables (can be overridden during build)
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
# Custom nginx config to handle SPA routing if necessary
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
