import { config as loadEnv } from 'dotenv';
import { z } from 'zod';

loadEnv();

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().int().min(1).max(65535).default(8787),
  HOST: z.string().min(1).default('0.0.0.0'),
  LOG_LEVEL: z.enum(['fatal', 'error', 'warn', 'info', 'debug', 'trace', 'silent']).default('info'),
  APP_NAME: z.string().min(1).default('CandyTravel API'),
  APP_BASE_URL: z.string().url().default('http://localhost:8787'),
  DATA_FILE_PATH: z.string().min(1).default('./data/candy-travel-db.json'),
});

export type AppConfig = z.infer<typeof envSchema>;

export const appConfig: AppConfig = envSchema.parse(process.env);
