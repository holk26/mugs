FROM node:22-alpine

WORKDIR /usr/src/app

RUN apk add --no-cache python3 make g++ \
  && corepack enable \
  && corepack prepare pnpm@11.1.2 --activate

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/core/package.json ./apps/core/package.json
COPY packages/printful/package.json ./packages/printful/package.json

RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 8080
CMD ["sh", "-c", "node apps/core/migrate.js && node apps/core/index.js"]
