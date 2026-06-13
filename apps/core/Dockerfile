# Dockerfile para storecraft-core-app
FROM node:20-alpine

WORKDIR /usr/src/app

RUN apk add --no-cache python3 make g++

COPY package*.json ./
RUN npm ci

COPY . .

RUN mkdir -p data storage

EXPOSE 8000
CMD npm run migrate && node index.js
