/**
 * API client for the Tourism API.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  [key: string]: unknown; // Allow additional fields like continents, countries, etc.
}

export async function fetchApi<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const json: ApiResponse<T> = await response.json();

  if (!json.success) {
    throw new Error(json.error || 'Unknown API error');
  }

  // If response has 'data' AND 'meta' fields, return full object (paginated response)
  // This handles { success, data: [...], meta: {...}, summary: {...} } format
  if (json.data !== undefined && 'meta' in json) {
    const { success, error, ...rest } = json;
    return rest as unknown as T;
  }

  // If response has only 'data' field without pagination, return just the data
  if (json.data !== undefined) {
    return json.data;
  }

  // Otherwise return the json without success/error fields
  // This handles { success, continents: [...], total: N } format
  const { success, error, ...rest } = json;
  return rest as unknown as T;
}
