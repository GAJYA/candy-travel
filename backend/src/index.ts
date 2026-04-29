import { appConfig } from './config.js';
import { createServer } from './server.js';

const app = createServer();

async function start() {
  try {
    await app.listen({
      host: appConfig.HOST,
      port: appConfig.PORT,
    });
  } catch (error) {
    app.log.error(error);
    process.exit(1);
  }
}

void start();
