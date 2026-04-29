import Fastify from 'fastify';
import { appConfig } from './config.js';
import { registerAiImportRoutes } from './routes/ai-import.js';
import { registerHealthRoutes } from './routes/health.js';
import { registerTripRoutes } from './routes/trips.js';

export function createServer() {
  const app = Fastify({
    logger: {
      level: appConfig.LOG_LEVEL,
    },
  });

  app.get('/', async () => {
    return {
      name: appConfig.APP_NAME,
      environment: appConfig.NODE_ENV,
      healthcheck: '/healthz',
    };
  });

  void registerHealthRoutes(app);
  void registerAiImportRoutes(app);
  void registerTripRoutes(app);

  return app;
}
