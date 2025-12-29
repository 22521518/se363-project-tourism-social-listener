import { locationRepository } from '../repositories/location.repository';
import { GeographyStats, Location, LocationType } from '../entities/location.entity';

// Color palette for geography types
const TYPE_COLORS: Record<LocationType, string> = {
  country: '#3b82f6',
  city: '#10b981',
  state: '#f59e0b',
  province: '#8b5cf6',
  landmark: '#ec4899',
  unknown: '#6b7280',
};

export class LocationService {
  /**
   * Aggregate locations by type for the "By Geography" chart.
   */
  async getGeographyStats(): Promise<GeographyStats[]> {
    const locations = await locationRepository.findAllLocationsFlat();

    // Count by type
    const countByType = new Map<LocationType, number>();
    for (const loc of locations) {
      const type = loc.type || 'unknown';
      countByType.set(type, (countByType.get(type) || 0) + 1);
    }

    // Convert to array sorted by count descending
    const stats: GeographyStats[] = [];
    for (const [type, count] of countByType.entries()) {
      stats.push({
        name: this.formatTypeName(type),
        value: count,
        color: TYPE_COLORS[type] || TYPE_COLORS.unknown,
      });
    }

    return stats.sort((a, b) => b.value - a.value);
  }

  private formatTypeName(type: LocationType): string {
    return type.charAt(0).toUpperCase() + type.slice(1);
  }
}

export const locationService = new LocationService();
