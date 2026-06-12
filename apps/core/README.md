# Mugs Core

Backend/API con **Storecraft** usando SQLite en desarrollo.

## Configuración

```bash
cp .env.example .env
# Completa las variables de Storecraft
```

## Desarrollo

```bash
npm install
npm run migrate
npm start
```

- API: http://localhost:8080/api
- Dashboard: http://localhost:8080/dashboard

## Docker

```bash
docker build -t mugs-core .
# o desde la raíz del monorepo
docker compose up --build
```

## Estructura

- `app.js` – configuración de Storecraft
- `index.js` – servidor HTTP
- `migrate.js` – migraciones de SQLite
- `Dockerfile` – imagen de producción
- `docker-compose.yml` – compose standalone del core
