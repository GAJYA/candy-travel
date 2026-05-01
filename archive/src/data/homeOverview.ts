import type {HomeOverviewStats, TripCountdown, UpcomingTrip} from '../types';
import {getStorageItem} from '../platform/storage';

const STORAGE_KEY = 'candy-travel-v1-trips';
const DAY_IN_MS = 24 * 60 * 60 * 1000;

const createRelativeDate = (offsetDays: number) => {
  const date = new Date();
  date.setHours(9, 30, 0, 0);
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString();
};

const seedTrips: UpcomingTrip[] = [
  {
    id: 'trip_tokyo',
    title: '东京樱花快闪',
    destinationCity: '日本东京',
    city: '日本东京',
    date: '',
    startDate: createRelativeDate(12),
    endDate: createRelativeDate(16),
    status: 'confirmed',
    iconBgClass: 'bg-primary-fixed group-hover:bg-primary',
    iconTextClass: 'text-primary group-hover:text-white',
    statusClass: 'bg-tertiary-fixed text-tertiary',
    kind: 'plane',
    distanceKm: 1760,
  },
  {
    id: 'trip_kyoto',
    title: '京都散策',
    destinationCity: '日本京都',
    city: '日本京都',
    date: '',
    startDate: createRelativeDate(34),
    endDate: createRelativeDate(38),
    status: 'confirmed',
    iconBgClass: 'bg-secondary-fixed group-hover:bg-secondary',
    iconTextClass: 'text-secondary group-hover:text-white',
    statusClass: 'bg-tertiary-fixed text-tertiary',
    kind: 'train',
    distanceKm: 460,
  },
  {
    id: 'trip_seoul',
    title: '首尔周末游',
    destinationCity: '韩国首尔',
    city: '韩国首尔',
    date: '',
    startDate: createRelativeDate(65),
    endDate: createRelativeDate(69),
    status: 'planning',
    iconBgClass: 'bg-primary-fixed group-hover:bg-primary',
    iconTextClass: 'text-primary group-hover:text-white',
    statusClass: 'bg-secondary-fixed text-secondary',
    kind: 'plane',
    distanceKm: 870,
  },
  {
    id: 'trip_bangkok',
    title: '曼谷慢旅行',
    destinationCity: '泰国曼谷',
    city: '泰国曼谷',
    date: '',
    startDate: createRelativeDate(93),
    endDate: createRelativeDate(99),
    status: 'draft',
    iconBgClass: 'bg-secondary-fixed group-hover:bg-secondary',
    iconTextClass: 'text-secondary group-hover:text-white',
    statusClass: 'bg-primary-fixed text-primary',
    kind: 'plane',
    distanceKm: 2890,
  },
];

const formatRange = (startDate: string, endDate: string) => {
  const formatter = new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
  });

  return `${formatter.format(new Date(startDate))} - ${formatter.format(new Date(endDate))}`;
};

const normalizeTrips = (trips: UpcomingTrip[]) =>
  trips
    .map((trip) => ({
      ...trip,
      date: formatRange(trip.startDate, trip.endDate),
    }))
    .sort((left, right) => new Date(left.startDate).getTime() - new Date(right.startDate).getTime());

export const loadUpcomingTrips = () => {
  const storedValue = getStorageItem(STORAGE_KEY);
  if (!storedValue) return normalizeTrips(seedTrips);

  try {
    const parsed = JSON.parse(storedValue) as UpcomingTrip[];
    if (!Array.isArray(parsed) || parsed.length === 0) {
      return normalizeTrips(seedTrips);
    }
    return normalizeTrips(parsed);
  } catch {
    return normalizeTrips(seedTrips);
  }
};

export const getHomeOverviewStats = (trips: UpcomingTrip[]): HomeOverviewStats => ({
  plannedCities: new Set(trips.map((trip) => trip.destinationCity)).size,
  tripCount: trips.length,
  distanceKm: trips.reduce((total, trip) => total + trip.distanceKm, 0),
});

export const getNextTripCountdown = (trips: UpcomingTrip[]): TripCountdown | null => {
  const now = Date.now();
  const nextTrip = trips.find((trip) => new Date(trip.startDate).getTime() > now);
  if (!nextTrip) return null;

  const remainingMs = Math.max(new Date(nextTrip.startDate).getTime() - now, 0);
  const days = String(Math.floor(remainingMs / DAY_IN_MS)).padStart(2, '0');
  const hours = String(Math.floor((remainingMs % DAY_IN_MS) / (60 * 60 * 1000))).padStart(2, '0');
  const minutes = String(Math.floor((remainingMs % (60 * 60 * 1000)) / (60 * 1000))).padStart(2, '0');

  return {
    days,
    hours,
    minutes,
    destinationCity: nextTrip.destinationCity,
  };
};
