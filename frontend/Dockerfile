# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package.json ./
RUN npm install

# Copy source files
COPY . .

# Build the app
# VITE_API_URL is set at build time - leave empty to use relative paths
# Explicitly unset any existing VITE_API_URL to ensure relative paths are used
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL:-}
RUN npm run build

# Production stage
FROM nginx:alpine

# Install wget for health checks
RUN apk add --no-cache wget

# Copy built files to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

