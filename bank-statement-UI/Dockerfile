# Frontend Dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm i

# Copy source code
COPY . .

# Expose port (adjust if your frontend runs on different port)
EXPOSE 8080

# Start the application
CMD ["npm", "run", "dev"]