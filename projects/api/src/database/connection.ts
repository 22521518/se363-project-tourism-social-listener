import { Pool } from 'pg';
import path from 'path';
import dotenv from 'dotenv';

// Load .env files - try multiple paths
const envPaths = [
  path.resolve(__dirname, '../../.env'),  // projects/api/.env
  path.resolve(__dirname, '../../../../.env'),  // airflow/.env (root)
];

for (const envPath of envPaths) {
  const result = dotenv.config({ path: envPath });
  if (!result.error) {
    console.log(`[Database] Loaded .env from: ${envPath}`);
  }
}

// Check for CA certificate
import fs from 'fs';
const caPath = path.resolve(__dirname, '../../ca.pem');
let sslConfig = undefined;

if (fs.existsSync(caPath)) {
  console.log(`[Database] Found CA certificate at: ${caPath}`);
  sslConfig = {
    rejectUnauthorized: true,
    ca: fs.readFileSync(caPath).toString(),
  };
}

// Database configuration with logging
const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  user: process.env.DB_USER || 'airflow',
  password: process.env.DB_PASSWORD || 'airflow',
  database: process.env.DB_NAME || 'airflow',
  max: 5,
  ssl: sslConfig,
};

// Log connection info (mask password)
console.log('============================================================');
console.log('[API] Database Connection Info');
console.log('============================================================');
console.log(`  Host    : ${dbConfig.host}`);
console.log(`  Port    : ${dbConfig.port}`);
console.log(`  Database: ${dbConfig.database}`);
console.log(`  User    : ${dbConfig.user}`);
console.log(`  URL     : postgresql://${dbConfig.user}:****@${dbConfig.host}:${dbConfig.port}/${dbConfig.database}`);
console.log(`  SSL     : ${sslConfig ? 'Enabled' : 'Disabled'}`);
console.log('============================================================');

const pool = new Pool(dbConfig);

export const query = async <T>(text: string, params?: unknown[]): Promise<T[]> => {
  const result = await pool.query(text, params);
  return result.rows as T[];
};

export const getPool = (): Pool => pool;
