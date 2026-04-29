import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type { FastifyInstance } from 'fastify';
import { ZodError, z } from 'zod';
import { appConfig } from '../config.js';

const transportModeSchema = z.enum(['flight', 'train', 'bus', 'car']);
const tripStatusSchema = z.enum(['draft', 'planning', 'confirmed', 'completed', 'archived']);
const tripSourceSchema = z.enum(['manual', 'ai_import']);
const tripEventTypeSchema = z.enum(['transport', 'stay', 'activity', 'reminder']);
const tripEventStatusSchema = z.enum(['draft', 'confirmed', 'canceled']);
const packingCategorySchema = z.enum(['document', 'electronics', 'clothing', 'medicine', 'food', 'other']);
const packingSourceSchema = z.enum(['manual', 'ai_generated']);
const isoDateSchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Expected YYYY-MM-DD');
const isoDateTimeSchema = z.string().datetime({ offset: true });

const tripDaySchema = z.object({
  id: z.string().min(1),
  date: isoDateSchema,
  summary: z.string().default(''),
  hint: z.string().default(''),
  highlightTag: z.string().default(''),
  sortOrder: z.number().int().nonnegative().default(0),
  createdAt: isoDateTimeSchema,
  updatedAt: isoDateTimeSchema,
});

const tripEventSchema = z.object({
  id: z.string().min(1),
  tripDayId: z.string().min(1).optional(),
  eventType: tripEventTypeSchema,
  title: z.string().min(1),
  description: z.string().default(''),
  startAt: isoDateTimeSchema,
  endAt: isoDateTimeSchema.optional(),
  locationName: z.string().optional(),
  address: z.string().optional(),
  transportMode: transportModeSchema.optional(),
  referenceCode: z.string().optional(),
  source: tripSourceSchema,
  status: tripEventStatusSchema.default('draft'),
  meta: z.record(z.string(), z.string()).optional(),
  createdAt: isoDateTimeSchema,
  updatedAt: isoDateTimeSchema,
});

const packingItemSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  checked: z.boolean().default(false),
  category: packingCategorySchema.default('other'),
  source: packingSourceSchema.default('manual'),
  sortOrder: z.number().int().nonnegative().default(0),
  createdAt: isoDateTimeSchema,
  updatedAt: isoDateTimeSchema,
});

const tripSchema = z
  .object({
    id: z.string().min(1),
    title: z.string().min(1),
    status: tripStatusSchema.default('draft'),
    startDate: isoDateSchema,
    endDate: isoDateSchema,
    originCity: z.string().default(''),
    destinationCity: z.string().default(''),
    primaryTransportMode: transportModeSchema.default('flight'),
    hotelName: z.string().default(''),
    note: z.string().default(''),
    countdownAnchorAt: isoDateTimeSchema,
    createdVia: tripSourceSchema.default('manual'),
    coverImageUrl: z.string().url().optional(),
    days: z.array(tripDaySchema).default([]),
    events: z.array(tripEventSchema).default([]),
    packingItems: z.array(packingItemSchema).default([]),
    createdAt: isoDateTimeSchema,
    updatedAt: isoDateTimeSchema,
  })
  .refine((trip) => trip.startDate <= trip.endDate, {
    message: 'startDate must be before or equal to endDate',
    path: ['startDate'],
  });

const dbSchema = z.object({
  trips: z.array(tripSchema).default([]),
});

const tripBodyBaseSchema = z.object({
  title: z.string().min(1),
  status: tripStatusSchema.optional(),
  startDate: isoDateSchema,
  endDate: isoDateSchema,
  originCity: z.string().optional(),
  destinationCity: z.string().optional(),
  primaryTransportMode: transportModeSchema.optional(),
  hotelName: z.string().optional(),
  note: z.string().optional(),
  countdownAnchorAt: isoDateTimeSchema.optional(),
  createdVia: tripSourceSchema.optional(),
  coverImageUrl: z.string().url().optional(),
});

const createTripBodySchema = tripBodyBaseSchema.refine((trip) => trip.startDate <= trip.endDate, {
    message: 'startDate must be before or equal to endDate',
    path: ['startDate'],
  });

const patchTripBodySchema = tripBodyBaseSchema.partial().refine((trip) => !trip.startDate || !trip.endDate || trip.startDate <= trip.endDate, {
  message: 'startDate must be before or equal to endDate',
  path: ['startDate'],
});

const createTripDayBodySchema = z.object({
  date: isoDateSchema,
  summary: z.string().default(''),
  hint: z.string().default(''),
  highlightTag: z.string().default(''),
  sortOrder: z.number().int().nonnegative().optional(),
});

const patchTripDayBodySchema = createTripDayBodySchema.partial();

const createTripEventBodySchema = z.object({
  tripDayId: z.string().min(1).optional(),
  eventType: tripEventTypeSchema,
  title: z.string().min(1),
  description: z.string().default(''),
  startAt: isoDateTimeSchema,
  endAt: isoDateTimeSchema.optional(),
  locationName: z.string().optional(),
  address: z.string().optional(),
  transportMode: transportModeSchema.optional(),
  referenceCode: z.string().optional(),
  source: tripSourceSchema.default('manual'),
  status: tripEventStatusSchema.default('draft'),
  meta: z.record(z.string(), z.string()).optional(),
});

const patchTripEventBodySchema = createTripEventBodySchema.partial();

const createPackingItemBodySchema = z.object({
  label: z.string().min(1),
  checked: z.boolean().optional(),
  category: packingCategorySchema.optional(),
  source: packingSourceSchema.optional(),
  sortOrder: z.number().int().nonnegative().optional(),
});

const patchPackingItemBodySchema = createPackingItemBodySchema.partial();
const calendarQuerySchema = z.object({ month: z.string().regex(/^\d{4}-\d{2}$/).optional() });

type TripRecord = z.infer<typeof tripSchema>;
type TripDay = z.infer<typeof tripDaySchema>;
type TripEvent = z.infer<typeof tripEventSchema>;
type PackingItem = z.infer<typeof packingItemSchema>;
type Database = z.infer<typeof dbSchema>;

const backendRoot = path.resolve(fileURLToPath(new URL('../../', import.meta.url)));
const databasePath = path.resolve(backendRoot, appConfig.DATA_FILE_PATH);

const nowIso = () => new Date().toISOString();
const createId = (prefix: string) => `${prefix}_${Math.random().toString(36).slice(2, 10)}`;

const sortDays = (days: TripDay[]) =>
  [...days].sort((left, right) => (left.date === right.date ? left.sortOrder - right.sortOrder : left.date.localeCompare(right.date)));

const sortEvents = (events: TripEvent[]) =>
  [...events].sort((left, right) => (left.startAt === right.startAt ? left.title.localeCompare(right.title) : left.startAt.localeCompare(right.startAt)));

const sortPackingItems = (items: PackingItem[]) => [...items].sort((left, right) => left.sortOrder - right.sortOrder);
const sortTrips = (trips: TripRecord[]) => [...trips].sort((left, right) => left.startDate.localeCompare(right.startDate));

function normalizeTrip(trip: TripRecord): TripRecord {
  return {
    ...trip,
    days: sortDays(trip.days),
    events: sortEvents(trip.events),
    packingItems: sortPackingItems(trip.packingItems),
  };
}

async function ensureDatabaseFile() {
  await mkdir(path.dirname(databasePath), { recursive: true });

  try {
    await readFile(databasePath, 'utf-8');
  } catch {
    await writeFile(databasePath, JSON.stringify({ trips: [] }, null, 2), 'utf-8');
  }
}

async function readDatabase() {
  await ensureDatabaseFile();
  const raw = await readFile(databasePath, 'utf-8');
  return dbSchema.parse(JSON.parse(raw));
}

async function writeDatabase(database: Database) {
  await ensureDatabaseFile();
  await writeFile(databasePath, JSON.stringify(database, null, 2), 'utf-8');
}

function badRequest(message: string) {
  const error = new Error(message) as Error & { statusCode?: number };
  error.statusCode = 400;
  return error;
}

function notFound(message: string) {
  const error = new Error(message) as Error & { statusCode?: number };
  error.statusCode = 404;
  return error;
}

function toHttpError(error: unknown) {
  if (error instanceof ZodError) {
    return badRequest(error.issues.map((issue) => `${issue.path.join('.') || 'body'}: ${issue.message}`).join('; '));
  }

  if (error instanceof Error) {
    return badRequest(error.message);
  }

  return badRequest('Unknown request error');
}

function assertDayWithinTrip(trip: TripRecord, date: string) {
  if (date < trip.startDate || date > trip.endDate) {
    throw new Error('Trip day date must be within trip range');
  }
}

function assertTripDayBelongsToTrip(trip: TripRecord, tripDayId?: string) {
  if (!tripDayId) return;
  if (!trip.days.some((day) => day.id === tripDayId)) {
    throw new Error('tripDayId does not belong to the target trip');
  }
}

async function withTrip(tripId: string, updater: (trip: TripRecord) => TripRecord) {
  const database = await readDatabase();
  const tripIndex = database.trips.findIndex((trip) => trip.id === tripId);

  if (tripIndex === -1) return null;

  const updatedTrip = normalizeTrip({
    ...updater(database.trips[tripIndex]),
    updatedAt: nowIso(),
  });

  database.trips[tripIndex] = updatedTrip;
  database.trips = sortTrips(database.trips);
  await writeDatabase(database);
  return updatedTrip;
}

export async function registerTripRoutes(app: FastifyInstance) {
  app.get('/api/v1/home', async () => {
    const database = await readDatabase();
    const trips = sortTrips(database.trips).map(normalizeTrip);
    const uniqueCities = new Set(trips.map((trip) => trip.destinationCity).filter(Boolean));

    return {
      upcomingTrips: trips.map((trip) => ({
        id: trip.id,
        title: trip.title,
        destinationCity: trip.destinationCity,
        startDate: trip.startDate,
        endDate: trip.endDate,
        status: trip.status,
        primaryTransportMode: trip.primaryTransportMode,
      })),
      stats: {
        plannedCities: uniqueCities.size,
        tripCount: trips.length,
        confirmedTripCount: trips.filter((trip) => trip.status === 'confirmed').length,
      },
    };
  });

  app.get('/api/v1/trips', async () => {
    const database = await readDatabase();
    return {
      items: sortTrips(database.trips).map(normalizeTrip),
    };
  });

  app.post('/api/v1/trips', async (request, reply) => {
    try {
      const body = createTripBodySchema.parse(request.body);
      const database = await readDatabase();
      const timestamp = nowIso();

      const item = normalizeTrip({
        id: createId('trip'),
        title: body.title,
        status: body.status ?? 'draft',
        startDate: body.startDate,
        endDate: body.endDate,
        originCity: body.originCity ?? '',
        destinationCity: body.destinationCity ?? '',
        primaryTransportMode: body.primaryTransportMode ?? 'flight',
        hotelName: body.hotelName ?? '',
        note: body.note ?? '',
        countdownAnchorAt: body.countdownAnchorAt ?? new Date(`${body.startDate}T09:00:00.000Z`).toISOString(),
        createdVia: body.createdVia ?? 'manual',
        coverImageUrl: body.coverImageUrl,
        days: [],
        events: [],
        packingItems: [],
        createdAt: timestamp,
        updatedAt: timestamp,
      });

      database.trips = sortTrips([...database.trips, item]);
      await writeDatabase(database);
      return reply.code(201).send({ item });
    } catch (error) {
      throw toHttpError(error);
    }
  });

  app.get('/api/v1/trips/:tripId', async (request) => {
    const { tripId } = request.params as { tripId: string };
    const database = await readDatabase();
    const item = database.trips.find((trip) => trip.id === tripId);

    if (!item) throw notFound('Trip not found');
    return { item: normalizeTrip(item) };
  });

  app.patch('/api/v1/trips/:tripId', async (request) => {
    try {
      const { tripId } = request.params as { tripId: string };
      const body = patchTripBodySchema.parse(request.body);
      const item = await withTrip(tripId, (trip) => {
        const nextTrip = { ...trip, ...body };
        if (nextTrip.startDate > nextTrip.endDate) {
          throw new Error('startDate must be before or equal to endDate');
        }
        return nextTrip;
      });

      if (!item) throw notFound('Trip not found');
      return { item };
    } catch (error) {
      throw toHttpError(error);
    }
  });

  app.get('/api/v1/trips/:tripId/calendar', async (request) => {
    try {
      const { tripId } = request.params as { tripId: string };
      const { month } = calendarQuerySchema.parse(request.query);
      const database = await readDatabase();
      const trip = database.trips.find((item) => item.id === tripId);

      if (!trip) throw notFound('Trip not found');

      return {
        tripId,
        trip: {
          id: trip.id,
          title: trip.title,
          status: trip.status,
          startDate: trip.startDate,
          endDate: trip.endDate,
          destinationCity: trip.destinationCity,
        },
        days: month ? trip.days.filter((day) => day.date.startsWith(`${month}-`)) : sortDays(trip.days),
        events: month ? trip.events.filter((event) => event.startAt.slice(0, 7) === month) : sortEvents(trip.events),
      };
    } catch (error) {
      throw toHttpError(error);
    }
  });

  app.get('/api/v1/trips/:tripId/days/:date', async (request) => {
    const { tripId, date } = request.params as { tripId: string; date: string };
    const database = await readDatabase();
    const trip = database.trips.find((item) => item.id === tripId);
    if (!trip) throw notFound('Trip not found');

    const day = trip.days.find((item) => item.date === date);
    if (!day) throw notFound('Trip day not found');

    return {
      tripId,
      day,
      events: sortEvents(trip.events.filter((event) => event.tripDayId === day.id)),
    };
  });

  app.post('/api/v1/trips/:tripId/days', async (request, reply) => {
    try {
      const { tripId } = request.params as { tripId: string };
      const body = createTripDayBodySchema.parse(request.body);
      const item = await withTrip(tripId, (trip) => {
        assertDayWithinTrip(trip, body.date);
        const timestamp = nowIso();
        const sameDateCount = trip.days.filter((day) => day.date === body.date).length;

        return {
          ...trip,
          days: [
            ...trip.days,
            {
              id: createId('day'),
              date: body.date,
              summary: body.summary,
              hint: body.hint,
              highlightTag: body.highlightTag,
              sortOrder: body.sortOrder ?? sameDateCount,
              createdAt: timestamp,
              updatedAt: timestamp,
            },
          ],
        };
      });

      if (!item) throw notFound('Trip not found');
      return reply.code(201).send({ item });
    } catch (error) {
      throw toHttpError(error);
    }
  });

  app.patch('/api/v1/trips/:tripId/days/:dayId', async (request) => {
    try {
      const { tripId, dayId } = request.params as { tripId: string; dayId: string };
      const body = patchTripDayBodySchema.parse(request.body);
      const item = await withTrip(tripId, (trip) => {
        const existing = trip.days.find((day) => day.id === dayId);
        if (!existing) throw new Error('Trip day not found');

        const nextDate = body.date ?? existing.date;
        assertDayWithinTrip(trip, nextDate);

        return {
          ...trip,
          days: trip.days.map((day) =>
            day.id === dayId
              ? {
                  ...day,
                  ...body,
                  updatedAt: nowIso(),
                }
              : day,
          ),
        };
      });

      if (!item) throw notFound('Trip not found');
      return { item };
    } catch (error) {
      throw toHttpError(error);
    }
  });

  app.delete('/api/v1/trips/:tripId/days/:dayId', async (request) => {
    const { tripId, dayId } = request.params as { tripId: string; dayId: string };
    const item = await withTrip(tripId, (trip) => ({
      ...trip,
      days: trip.days.filter((day) => day.id !== dayId),
      events: trip.events.map((event) => (event.tripDayId === dayId ? { ...event, tripDayId: undefined, updatedAt: nowIso() } : event)),
    }));

    if (!item) throw notFound('Trip not found');
    return { item };
  });

  app.post('/api/v1/trips/:tripId/events', async (request, reply) => {
    try {
      const { tripId } = request.params as { tripId: string };
      const body = createTripEventBodySchema.parse(request.body);
      const item = await withTrip(tripId, (trip) => {
        assertTripDayBelongsToTrip(trip, body.tripDayId);
        const timestamp = nowIso();

        return {
          ...trip,
          events: [
            ...trip.events,
            {
              id: createId('event'),
              tripDayId: body.tripDayId,
              eventType: body.eventType,
              title: body.title,
              description: body.description,
              startAt: body.startAt,
              endAt: body.endAt,
              locationName: body.locationName,
              address: body.address,
              transportMode: body.transportMode,
              referenceCode: body.referenceCode,
              source: body.source,
              status: body.status,
              meta: body.meta,
              createdAt: timestamp,
              updatedAt: timestamp,
            },
          ],
        };
      });

      if (!item) throw notFound('Trip not found');
      return reply.code(201).send({ item });
    } catch (error) {
      throw toHttpError(error);
    }
  });

  app.patch('/api/v1/events/:eventId', async (request) => {
    try {
      const { eventId } = request.params as { eventId: string };
      const body = patchTripEventBodySchema.parse(request.body);
      const database = await readDatabase();
      let matchedTripId: string | null = null;

      for (const trip of database.trips) {
        if (!trip.events.some((event) => event.id === eventId)) continue;
        matchedTripId = trip.id;
        break;
      }

      if (!matchedTripId) throw notFound('Trip event not found');

      const item = await withTrip(matchedTripId, (trip) => {
        const current = trip.events.find((event) => event.id === eventId);
        if (!current) throw new Error('Trip event not found');
        assertTripDayBelongsToTrip(trip, body.tripDayId ?? current.tripDayId);

        return {
          ...trip,
          events: trip.events.map((event) =>
            event.id === eventId
              ? {
                  ...event,
                  ...body,
                  updatedAt: nowIso(),
                }
              : event,
          ),
        };
      });

      return { item };
    } catch (error) {
      throw toHttpError(error);
    }
  });

  app.delete('/api/v1/events/:eventId', async (request) => {
    const { eventId } = request.params as { eventId: string };
    const database = await readDatabase();
    const trip = database.trips.find((item) => item.events.some((event) => event.id === eventId));
    if (!trip) throw notFound('Trip event not found');

    const item = await withTrip(trip.id, (currentTrip) => ({
      ...currentTrip,
      events: currentTrip.events.filter((event) => event.id !== eventId),
    }));

    return { item };
  });

  app.get('/api/v1/trips/:tripId/packing-items', async (request) => {
    const { tripId } = request.params as { tripId: string };
    const database = await readDatabase();
    const trip = database.trips.find((item) => item.id === tripId);
    if (!trip) throw notFound('Trip not found');

    return {
      tripId,
      items: sortPackingItems(trip.packingItems),
    };
  });

  app.post('/api/v1/trips/:tripId/packing-items', async (request, reply) => {
    try {
      const { tripId } = request.params as { tripId: string };
      const body = createPackingItemBodySchema.parse(request.body);
      const item = await withTrip(tripId, (trip) => {
        const timestamp = nowIso();
        return {
          ...trip,
          packingItems: [
            ...trip.packingItems,
            {
              id: createId('packing'),
              label: body.label,
              checked: body.checked ?? false,
              category: body.category ?? 'other',
              source: body.source ?? 'manual',
              sortOrder: body.sortOrder ?? trip.packingItems.length,
              createdAt: timestamp,
              updatedAt: timestamp,
            },
          ],
        };
      });

      if (!item) throw notFound('Trip not found');
      return reply.code(201).send({ item });
    } catch (error) {
      throw toHttpError(error);
    }
  });

  app.patch('/api/v1/packing-items/:itemId', async (request) => {
    try {
      const { itemId } = request.params as { itemId: string };
      const body = patchPackingItemBodySchema.parse(request.body);
      const database = await readDatabase();
      const trip = database.trips.find((item) => item.packingItems.some((packingItem) => packingItem.id === itemId));
      if (!trip) throw notFound('Packing item not found');

      const item = await withTrip(trip.id, (currentTrip) => ({
        ...currentTrip,
        packingItems: currentTrip.packingItems.map((packingItem) =>
          packingItem.id === itemId
            ? {
                ...packingItem,
                ...body,
                updatedAt: nowIso(),
              }
            : packingItem,
        ),
      }));

      return { item };
    } catch (error) {
      throw toHttpError(error);
    }
  });

  app.delete('/api/v1/packing-items/:itemId', async (request) => {
    const { itemId } = request.params as { itemId: string };
    const database = await readDatabase();
    const trip = database.trips.find((item) => item.packingItems.some((packingItem) => packingItem.id === itemId));
    if (!trip) throw notFound('Packing item not found');

    const item = await withTrip(trip.id, (currentTrip) => ({
      ...currentTrip,
      packingItems: currentTrip.packingItems.filter((packingItem) => packingItem.id !== itemId),
    }));

    return { item };
  });
}
