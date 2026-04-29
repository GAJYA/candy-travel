export type TabId = 'home' | 'calendar' | 'ai' | 'profile';

export type TransportMode = 'flight' | 'train' | 'bus' | 'car';
export type TripStatus = 'draft' | 'planning' | 'confirmed' | 'completed';
export type TripSource = 'manual' | 'ai_import';
export type TripEventType = 'transport' | 'stay' | 'activity' | 'reminder';
export type TripEventStatus = 'draft' | 'confirmed' | 'canceled';
export type PackingCategory = 'document' | 'electronics' | 'clothing' | 'medicine' | 'food' | 'other';
export type PackingSource = 'manual' | 'ai_generated';

export interface UpcomingTrip {
  id: string;
  title: string;
  destinationCity: string;
  city: string;
  date: string;
  startDate: string;
  endDate: string;
  status: TripStatus;
  iconBgClass: string;
  iconTextClass: string;
  statusClass: string;
  kind: 'plane' | 'train';
  distanceKm: number;
}

export interface CalendarActivity {
  title: string;
  time: string;
  description: string;
  meta: string;
  tone: 'tertiary' | 'secondary';
  icon: 'utensils' | 'landmark';
  metaIcon: 'map-pin' | 'ticket';
}

export interface PackingItem {
  label: string;
  checked: boolean;
}

export interface TripCountdown {
  days: string;
  hours: string;
  minutes: string;
  destinationCity: string;
}

export interface HomeOverviewStats {
  plannedCities: number;
  tripCount: number;
  distanceKm: number;
}

export interface TripDay {
  id: string;
  date: string;
  summary: string;
  hint: string;
  highlightTag: string;
  sortOrder: number;
}

export interface TripEvent {
  id: string;
  tripDayId?: string;
  eventType: TripEventType;
  title: string;
  description: string;
  startAt: string;
  endAt?: string;
  locationName?: string;
  address?: string;
  transportMode?: TransportMode;
  referenceCode?: string;
  source: TripSource;
  status: TripEventStatus;
  meta?: Record<string, string>;
}

export interface TripPackingItem {
  id: string;
  label: string;
  checked: boolean;
  category: PackingCategory;
  source: PackingSource;
  sortOrder: number;
}

export interface TripRecord {
  id: string;
  title: string;
  status: TripStatus;
  startDate: string;
  endDate: string;
  originCity: string;
  destinationCity: string;
  primaryTransportMode: TransportMode;
  hotelName: string;
  note: string;
  countdownAnchorAt: string;
  createdVia: TripSource;
  coverImageUrl?: string;
  days: TripDay[];
  events: TripEvent[];
  packingItems: TripPackingItem[];
  createdAt: string;
  updatedAt: string;
}
