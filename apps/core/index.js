import 'dotenv/config';
import http from "node:http";
import { app } from './app.js';
 
const PORT = process.env.PORT ? parseInt(process.env.PORT) : 8080;
http.createServer(app.handler).listen(
  PORT,
  () => { app.print_banner(`http://localhost:${PORT}`) }
);
