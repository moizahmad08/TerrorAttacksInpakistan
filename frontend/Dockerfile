# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Ensure production API URL is baked into the build (relative /api via nginx)
COPY .env.production .env.production
ENV VITE_API_URL=/api
RUN npm run build

# Serve stage
FROM nginx:alpine
# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html
# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
