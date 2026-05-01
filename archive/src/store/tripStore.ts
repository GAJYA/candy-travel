import {computed, reactive, watch} from 'vue';
import {getStorageItem, canUseStorage, removeStorageItem, setStorageItem} from '../platform/storage';
import type {
  PackingCategory,
  PackingSource,
  UpcomingTrip,
  TransportMode,
  TripDay,
  TripEvent,
  TripEventStatus,
  TripEventType,
  TripPackingItem,
  TripRecord,
  TripSource,
  TripStatus,
} from '../types';

export type {PackingCategory, PackingSource, TripDay, TripEvent, TripEventStatus, TripEventType, TripPackingItem, TripRecord, TripSource};

type TripStoreState = {
  selectedTripId: string;
  trips: TripRecord[];
};

type CreateTripInput = Partial<Omit<TripRecord, 'id' | 'days' | 'events' | 'packingItems' | 'createdAt' | 'updatedAt'>>;
type UpsertTripDayInput = Omit<TripDay, 'id'> & {id?: string};
type UpsertTripEventInput = Omit<TripEvent, 'id'> & {id?: string};
type UpsertPackingItemInput = Omit<TripPackingItem, 'id'> & {id?: string};

const STORAGE_KEY = 'candy-travel-trip-store-v1';
const HOME_OVERVIEW_STORAGE_KEY = 'candy-travel-v1-trips';

const statusOrder: Record<TripStatus, number> = {
  planning: 0,
  confirmed: 1,
  draft: 2,
  completed: 3,
};

const createId = (prefix: string) => `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
const nowIso = () => new Date().toISOString();

const shiftDate = (offsetDays: number, hour = 9, minute = 30) => {
  const date = new Date();
  date.setHours(hour, minute, 0, 0);
  date.setDate(date.getDate() + offsetDays);
  return date;
};

const formatDateOnly = (date: Date) => {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const formatDateRange = (startDate: string, endDate: string) => {
  const formatter = new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
  });

  return `${formatter.format(new Date(`${startDate}T00:00:00`))} - ${formatter.format(new Date(`${endDate}T00:00:00`))}`;
};

const sortTripDays = (days: TripDay[]) =>
  [...days].sort((left, right) => {
    if (left.date === right.date) return left.sortOrder - right.sortOrder;
    return left.date.localeCompare(right.date);
  });

const sortTripEvents = (events: TripEvent[]) =>
  [...events].sort((left, right) => {
    if (left.startAt === right.startAt) return left.title.localeCompare(right.title);
    return left.startAt.localeCompare(right.startAt);
  });

const sortPackingItems = (items: TripPackingItem[]) =>
  [...items].sort((left, right) => left.sortOrder - right.sortOrder);

const normalizeTrips = (trips: TripRecord[]) =>
  [...trips]
    .map((trip) => ({
      ...trip,
      days: sortTripDays(trip.days),
      events: sortTripEvents(trip.events),
      packingItems: sortPackingItems(trip.packingItems),
    }))
    .sort((left, right) => {
      const statusCompare = statusOrder[left.status] - statusOrder[right.status];
      if (statusCompare !== 0) return statusCompare;
      return left.startDate.localeCompare(right.startDate);
    });

export const toHomeOverviewSnapshot = (trips: TripRecord[]): UpcomingTrip[] => {
  return trips.map((trip) => ({
    id: trip.id,
    title: trip.title,
    destinationCity: trip.destinationCity,
    city: trip.destinationCity,
    date: formatDateRange(trip.startDate, trip.endDate),
    startDate: trip.countdownAnchorAt,
    endDate: new Date(`${trip.endDate}T18:00:00`).toISOString(),
    status: trip.status,
    iconBgClass: trip.primaryTransportMode === 'train' ? 'bg-secondary-fixed group-hover:bg-secondary' : 'bg-primary-fixed group-hover:bg-primary',
    iconTextClass: trip.primaryTransportMode === 'train' ? 'text-secondary group-hover:text-white' : 'text-primary group-hover:text-white',
    statusClass:
      trip.status === 'confirmed'
        ? 'bg-tertiary-fixed text-tertiary'
        : trip.status === 'planning'
          ? 'bg-secondary-fixed text-secondary'
          : 'bg-primary-fixed text-primary',
    kind: trip.primaryTransportMode === 'train' ? 'train' : 'plane',
    distanceKm: trip.primaryTransportMode === 'train' ? 460 : 1760,
  }));
};

const createSeedTrips = (): TripRecord[] => {
  const createdAt = nowIso();
  const kyotoStart = shiftDate(12, 8, 40);
  const kyotoWalk = shiftDate(13, 9, 30);
  const kyotoMuseum = shiftDate(13, 15, 0);
  const kyotoTrain = shiftDate(15, 10, 20);
  const seoulStart = shiftDate(34, 10, 0);

  return [
    {
      id: 'trip_kyoto',
      title: '京都樱花之旅',
      status: 'confirmed',
      startDate: formatDateOnly(kyotoStart),
      endDate: formatDateOnly(shiftDate(16, 18, 0)),
      originCity: '上海',
      destinationCity: '日本京都',
      primaryTransportMode: 'train',
      hotelName: '樱花皇宫大酒店',
      note: '重点看樱花、轻松逛街，保留一晚自由活动。',
      countdownAnchorAt: kyotoStart.toISOString(),
      createdVia: 'manual',
      coverImageUrl: 'https://picsum.photos/seed/travel-map/600/300',
      createdAt,
      updatedAt: createdAt,
      days: [
        {
          id: 'day_kyoto_depart',
          date: formatDateOnly(kyotoStart),
          summary: '出发日',
          hint: '今天正式启程，记得提前在线值机并预留足够的机场交通时间。',
          highlightTag: '出发',
          sortOrder: 0,
        },
        {
          id: 'day_kyoto_walk',
          date: formatDateOnly(kyotoWalk),
          summary: '城市探索',
          hint: '轻松适应旅程节奏，优先安排步行可达的点位。',
          highlightTag: '漫游',
          sortOrder: 1,
        },
        {
          id: 'day_kyoto_transfer',
          date: formatDateOnly(kyotoTrain),
          summary: '换城日',
          hint: '今天改乘新干线前往京都，站内换乘信息已提前整理好。',
          highlightTag: '移动',
          sortOrder: 2,
        },
      ],
      events: [
        {
          id: 'event_kyoto_flight',
          tripDayId: 'day_kyoto_depart',
          eventType: 'transport',
          title: '飞往东京',
          description: '国际航班 MU523，值机和托运都已准备好。',
          startAt: kyotoStart.toISOString(),
          endAt: shiftDate(12, 12, 30).toISOString(),
          locationName: '浦东国际机场 T1',
          transportMode: 'flight',
          referenceCode: 'MU523',
          source: 'manual',
          status: 'confirmed',
          meta: {tone: 'tertiary', metaIcon: 'map-pin'},
        },
        {
          id: 'event_kyoto_asakusa',
          tripDayId: 'day_kyoto_walk',
          eventType: 'activity',
          title: '浅草寺晨间散步',
          description: '拍照、抽签并顺路吃一份热腾腾的人形烧。',
          startAt: kyotoWalk.toISOString(),
          locationName: '台东区浅草',
          source: 'manual',
          status: 'confirmed',
          meta: {tone: 'tertiary', metaIcon: 'map-pin'},
        },
        {
          id: 'event_kyoto_teamlab',
          tripDayId: 'day_kyoto_walk',
          eventType: 'activity',
          title: 'teamLab Borderless',
          description: '提前 15 分钟到场，门票已预订。',
          startAt: kyotoMuseum.toISOString(),
          referenceCode: '电子门票已确认',
          source: 'manual',
          status: 'confirmed',
          meta: {tone: 'secondary', metaIcon: 'ticket'},
        },
        {
          id: 'event_kyoto_train',
          tripDayId: 'day_kyoto_transfer',
          eventType: 'transport',
          title: '东京站出发去京都',
          description: '乘坐东海道新干线 Nozomi，车票已出票。',
          startAt: kyotoTrain.toISOString(),
          locationName: '东京站 18 号站台',
          transportMode: 'train',
          referenceCode: 'Nozomi',
          source: 'manual',
          status: 'confirmed',
          meta: {tone: 'secondary', metaIcon: 'ticket'},
        },
      ],
      packingItems: [
        {id: 'packing_camera', label: '相机与镜头', checked: true, category: 'electronics', source: 'manual', sortOrder: 0},
        {id: 'packing_powerbank', label: '便携式充电器', checked: false, category: 'electronics', source: 'manual', sortOrder: 1},
        {id: 'packing_passport', label: '护照', checked: true, category: 'document', source: 'manual', sortOrder: 2},
      ],
    },
    {
      id: 'trip_seoul',
      title: '首尔周末快闪',
      status: 'planning',
      startDate: formatDateOnly(seoulStart),
      endDate: formatDateOnly(shiftDate(38, 18, 0)),
      originCity: '上海',
      destinationCity: '韩国首尔',
      primaryTransportMode: 'flight',
      hotelName: '明洞城市酒店',
      note: '以美食和买手店为主，保留半天自由行程。',
      countdownAnchorAt: seoulStart.toISOString(),
      createdVia: 'ai_import',
      coverImageUrl: 'https://picsum.photos/seed/seoul/600/300',
      createdAt,
      updatedAt: createdAt,
      days: [
        {
          id: 'day_seoul_arrival',
          date: formatDateOnly(seoulStart),
          summary: '抵达首尔',
          hint: '落地后先去酒店放行李，再安排晚餐。',
          highlightTag: '抵达',
          sortOrder: 0,
        },
      ],
      events: [
        {
          id: 'event_seoul_flight',
          tripDayId: 'day_seoul_arrival',
          eventType: 'transport',
          title: '飞往首尔',
          description: '航班时间待最终确认。',
          startAt: seoulStart.toISOString(),
          transportMode: 'flight',
          source: 'ai_import',
          status: 'draft',
          meta: {tone: 'secondary', metaIcon: 'ticket'},
        },
      ],
      packingItems: [
        {id: 'packing_id_card', label: '电子身份证', checked: true, category: 'document', source: 'ai_generated', sortOrder: 0},
        {id: 'packing_receipt', label: '电子票据', checked: true, category: 'document', source: 'ai_generated', sortOrder: 1},
        {id: 'packing_sunscreen', label: '防晒霜', checked: false, category: 'other', source: 'ai_generated', sortOrder: 2},
      ],
    },
  ];
};

const createInitialState = (): TripStoreState => {
  const trips = normalizeTrips(createSeedTrips());
  return {
    selectedTripId: trips[0]?.id ?? '',
    trips,
  };
};

const loadStoreState = (): TripStoreState => {
  if (!canUseStorage()) return createInitialState();

  const rawValue = getStorageItem(STORAGE_KEY);
  if (!rawValue) return createInitialState();

  try {
    const parsed = JSON.parse(rawValue) as TripStoreState;
    const trips = normalizeTrips(parsed.trips ?? []);
    return {
      selectedTripId: trips.some((trip) => trip.id === parsed.selectedTripId) ? parsed.selectedTripId : (trips[0]?.id ?? ''),
      trips,
    };
  } catch {
    return createInitialState();
  }
};

const state = reactive<TripStoreState>(loadStoreState());

watch(
  state,
  (nextState) => {
    if (!canUseStorage()) return;
    setStorageItem(STORAGE_KEY, JSON.stringify(nextState));
    setStorageItem(HOME_OVERVIEW_STORAGE_KEY, JSON.stringify(toHomeOverviewSnapshot(nextState.trips)));
  },
  {deep: true},
);

const selectedTrip = computed<TripRecord | null>(() => {
  return state.trips.find((trip) => trip.id === state.selectedTripId) ?? state.trips[0] ?? null;
});

const tripList = computed<TripRecord[]>(() => state.trips);

const touchTrip = (trip: TripRecord): TripRecord => ({
  ...trip,
  updatedAt: nowIso(),
});

const replaceTrip = (nextTrip: TripRecord) => {
  state.trips = normalizeTrips(state.trips.map((trip) => (trip.id === nextTrip.id ? nextTrip : trip)));
};

const getTripById = (tripId: string) => {
  return state.trips.find((trip) => trip.id === tripId) ?? null;
};

const selectTrip = (tripId: string) => {
  if (state.trips.some((trip) => trip.id === tripId)) {
    state.selectedTripId = tripId;
  }
};

const createTrip = (input: CreateTripInput = {}) => {
  const createdAt = nowIso();
  const today = formatDateOnly(new Date());
  const nextTrip: TripRecord = {
    id: createId('trip'),
    title: input.title ?? '新的旅行计划',
    status: input.status ?? 'planning',
    startDate: input.startDate ?? today,
    endDate: input.endDate ?? today,
    originCity: input.originCity ?? '上海',
    destinationCity: input.destinationCity ?? '新的目的地',
    primaryTransportMode: input.primaryTransportMode ?? 'flight',
    hotelName: input.hotelName ?? '',
    note: input.note ?? '',
    countdownAnchorAt: input.countdownAnchorAt ?? createdAt,
    createdVia: input.createdVia ?? 'manual',
    coverImageUrl: input.coverImageUrl,
    days: [],
    events: [],
    packingItems: [],
    createdAt,
    updatedAt: createdAt,
  };

  state.trips = normalizeTrips([...state.trips, nextTrip]);
  state.selectedTripId = nextTrip.id;
  return nextTrip;
};

const updateTrip = (tripId: string, patch: Partial<TripRecord>) => {
  const currentTrip = getTripById(tripId);
  if (!currentTrip) return null;

  const nextTrip = touchTrip({
    ...currentTrip,
    ...patch,
    id: currentTrip.id,
    days: patch.days ?? currentTrip.days,
    events: patch.events ?? currentTrip.events,
    packingItems: patch.packingItems ?? currentTrip.packingItems,
  });

  replaceTrip(nextTrip);
  return nextTrip;
};

const createDefaultDay = (date: string, sortOrder: number): TripDay => ({
  id: createId('day'),
  date,
  summary: '今天还没有安排行程',
  hint: '可以继续补充交通、活动或住宿安排。',
  highlightTag: '空闲',
  sortOrder,
});

const upsertTripDay = (tripId: string, input: UpsertTripDayInput) => {
  const currentTrip = getTripById(tripId);
  if (!currentTrip) return null;

  const existingDay = currentTrip.days.find((day: TripDay) => day.id === input.id || day.date === input.date);
  const nextDay: TripDay = {
    id: existingDay?.id ?? input.id ?? createId('day'),
    date: input.date,
    summary: input.summary,
    hint: input.hint,
    highlightTag: input.highlightTag,
    sortOrder: input.sortOrder,
  };

  const nextDays = existingDay
    ? currentTrip.days.map((day: TripDay) => (day.id === existingDay.id ? nextDay : day))
    : [...currentTrip.days, nextDay];

  replaceTrip(touchTrip({...currentTrip, days: nextDays}));
  return nextDay;
};

const ensureTripDay = (tripId: string, date: string) => {
  const currentTrip = getTripById(tripId);
  if (!currentTrip) return null;

  const existingDay = currentTrip.days.find((day: TripDay) => day.date === date);
  if (existingDay) return existingDay;

  return upsertTripDay(tripId, createDefaultDay(date, currentTrip.days.length));
};

const removeTripDay = (tripId: string, tripDayId: string) => {
  const currentTrip = getTripById(tripId);
  if (!currentTrip) return;

  replaceTrip(
    touchTrip({
      ...currentTrip,
      days: currentTrip.days.filter((day: TripDay) => day.id !== tripDayId),
      events: currentTrip.events.filter((event: TripEvent) => event.tripDayId !== tripDayId),
    }),
  );
};

const upsertTripEvent = (tripId: string, input: UpsertTripEventInput) => {
  const currentTrip = getTripById(tripId);
  if (!currentTrip) return null;

  const eventDate = input.startAt.slice(0, 10);
  const targetDay = input.tripDayId ? currentTrip.days.find((day) => day.id === input.tripDayId) : ensureTripDay(tripId, eventDate);
  const refreshedTrip = getTripById(tripId);
  if (!refreshedTrip) return null;

  const existingEvent = refreshedTrip.events.find((event: TripEvent) => event.id === input.id);
  const nextEvent: TripEvent = {
    id: existingEvent?.id ?? input.id ?? createId('event'),
    tripDayId: targetDay?.id,
    eventType: input.eventType,
    title: input.title,
    description: input.description,
    startAt: input.startAt,
    endAt: input.endAt,
    locationName: input.locationName,
    address: input.address,
    transportMode: input.transportMode,
    referenceCode: input.referenceCode,
    source: input.source,
    status: input.status,
    meta: input.meta,
  };

  const nextEvents = existingEvent
    ? refreshedTrip.events.map((event: TripEvent) => (event.id === existingEvent.id ? nextEvent : event))
    : [...refreshedTrip.events, nextEvent];

  replaceTrip(touchTrip({...refreshedTrip, events: nextEvents}));
  return nextEvent;
};

const removeTripEvent = (tripId: string, eventId: string) => {
  const currentTrip = getTripById(tripId);
  if (!currentTrip) return;

  replaceTrip(
    touchTrip({
      ...currentTrip,
      events: currentTrip.events.filter((event: TripEvent) => event.id !== eventId),
    }),
  );
};

const upsertPackingItem = (tripId: string, input: UpsertPackingItemInput) => {
  const currentTrip = getTripById(tripId);
  if (!currentTrip) return null;

  const existingItem = currentTrip.packingItems.find((item: TripPackingItem) => item.id === input.id);
  const nextItem: TripPackingItem = {
    id: existingItem?.id ?? input.id ?? createId('packing'),
    label: input.label,
    checked: input.checked,
    category: input.category,
    source: input.source,
    sortOrder: input.sortOrder,
  };

  const nextPackingItems = existingItem
    ? currentTrip.packingItems.map((item: TripPackingItem) => (item.id === existingItem.id ? nextItem : item))
    : [...currentTrip.packingItems, nextItem];

  replaceTrip(touchTrip({...currentTrip, packingItems: nextPackingItems}));
  return nextItem;
};

const togglePackingItem = (tripId: string, itemId: string) => {
  const currentTrip = getTripById(tripId);
  if (!currentTrip) return;

  replaceTrip(
    touchTrip({
      ...currentTrip,
      packingItems: currentTrip.packingItems.map((item: TripPackingItem) =>
        item.id === itemId ? {...item, checked: !item.checked} : item,
      ),
    }),
  );
};

const removePackingItem = (tripId: string, itemId: string) => {
  const currentTrip = getTripById(tripId);
  if (!currentTrip) return;

  replaceTrip(
    touchTrip({
      ...currentTrip,
      packingItems: currentTrip.packingItems.filter((item: TripPackingItem) => item.id !== itemId),
    }),
  );
};

const resetTripStore = () => {
  removeStorageItem(STORAGE_KEY);
  removeStorageItem(HOME_OVERVIEW_STORAGE_KEY);
  const nextState = createInitialState();
  state.selectedTripId = nextState.selectedTripId;
  state.trips = nextState.trips;
};

export const useTripStore = () => ({
  state,
  tripList,
  selectedTrip,
  getTripById,
  selectTrip,
  createTrip,
  updateTrip,
  upsertTripDay,
  ensureTripDay,
  removeTripDay,
  upsertTripEvent,
  removeTripEvent,
  upsertPackingItem,
  togglePackingItem,
  removePackingItem,
  resetTripStore,
});
