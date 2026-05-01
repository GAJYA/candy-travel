import type { FastifyInstance } from 'fastify';

export async function registerHealthRoutes(app: FastifyInstance) {
  const healthHandler = async () => {
    const timestamp = new Date().toISOString();

    return {
      ok: true,
      service: 'candy-travel-backend',
      timestamp,
      uptimeSeconds: Math.floor(process.uptime()),
    };
  };

  app.get('/healthz', healthHandler);
  app.get('/api/v1/healthz', healthHandler);
}
