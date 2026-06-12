# Dockerfile para storecraft-core-app
FROM node:20-alpine

WORKDIR /usr/src/app

RUN apk add --no-cache python3 make g++

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 8080
CMD npm run migrate && node index.js
