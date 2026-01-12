import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '../services/api';

export interface ContinentStats {
  id: string;
  name: string;
  count: number;
  countries: string[];
  color: string;
}

export interface CountryStats {
  id: string;
  name: string;
  continent: string;
  count: number;
  regions: string[];
}

export interface RegionStats {
  id: string;
  name: string;
  country: string;
  count: number;
}

interface ContinentResponse {
  success: boolean;
  continents: ContinentStats[];
  total: number;
}

interface CountryResponse {
  success: boolean;
  countries: CountryStats[];
  continent: string;
  total: number;
}

interface RegionResponse {
  success: boolean;
  regions: RegionStats[];
  country: string;
  total: number;
}

/**
 * Hook to fetch continent statistics
 */
export function useContinentData() {
  const [data, setData] = useState<ContinentStats[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetchApi<ContinentResponse>('/locations/continents');
      console.log('useContinentData raw response:', response);
      console.log('useContinentData continents:', response?.continents);
      setData(response?.continents || []);
      setTotal(response?.total || 0);
    } catch (err) {
      console.error('useContinentData error:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch continents');
      setData([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, total, loading, error, refetch: fetchData };
}

/**
 * Hook to fetch country statistics for a continent
 */
export function useCountryData(continentId: string | null) {
  const [data, setData] = useState<CountryStats[]>([]);
  const [continentName, setContinentName] = useState('');
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!continentId) {
      setData([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetchApi<CountryResponse>(
        `/locations/countries?continent=${continentId}`
      );
      setData(response?.countries || []);
      setContinentName(response?.continent || '');
      setTotal(response?.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch countries');
      setData([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [continentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, continentName, total, loading, error, refetch: fetchData };
}

/**
 * Hook to fetch region statistics for a country
 */
export function useRegionData(countryId: string | null) {
  const [data, setData] = useState<RegionStats[]>([]);
  const [countryName, setCountryName] = useState('');
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!countryId) {
      setData([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetchApi<RegionResponse>(
        `/locations/regions?country=${countryId}`
      );
      setData(response?.regions || []);
      setCountryName(response?.country || '');
      setTotal(response?.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch regions');
      setData([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [countryId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, countryName, total, loading, error, refetch: fetchData };
}
