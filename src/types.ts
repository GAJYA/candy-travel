export type TransportMode = 'flight' | 'train' | 'bus' | 'car';

export interface Activity {
  id: string;
  time: string;
  title: string;
  description: string;
  location?: string;
  type: 'restaurant' | 'museum' | 'transport' | 'other';
  status?: string;
}

export interface Trip {
  id: string;
  destination: string;
  startDate: string;
  endDate: string;
  status: 'confirmed' | 'planning' | 'draft';
  transportMode: TransportMode;
  activities: Activity[];
}

export interface UserStats {
  plannedCities: number;
  tripCount: number;
  totalDistanceKm: number;
}
