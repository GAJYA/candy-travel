export type TabId = 'home' | 'calendar' | 'ai' | 'profile';

export type TransportMode = 'flight' | 'train' | 'bus' | 'car';

export interface UpcomingTrip {
  city: string;
  date: string;
  status: 'confirmed' | 'planning';
  iconBgClass: string;
  iconTextClass: string;
  statusClass: string;
  kind: 'plane' | 'train';
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
