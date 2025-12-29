import { Pool } from 'pg';

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  user: process.env.DB_USER || 'airflow',
  password: process.env.DB_PASSWORD || 'airflow',
  database: process.env.DB_NAME || 'airflow',
});

export const query = async <T>(text: string, params?: unknown[]): Promise<T[]> => {
  const result = await pool.query(text, params);
  return result.rows as T[];
};

export const getPool = (): Pool => pool;
