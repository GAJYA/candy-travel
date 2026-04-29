import { randomUUID } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { z } from 'zod';
import type { FastifyInstance } from 'fastify';
import { appConfig } from '../config.js';

const createJobBodySchema = z.object({
  inputType: z.enum(['text']).default('text'),
  rawText: z.string().min(1),
  tripId: z.string().min(1).optional(),
});

const jobParamsSchema = z.object({
  jobId: z.string().min(1),
});

type DraftConfidence = 'high' | 'medium' | 'low';

type DraftField = {
  value: string;
  confidence: DraftConfidence;
};

type AiImportPayload = {
  tripDraft: {
    title: DraftField;
    startDate: DraftField;
    endDate: DraftField;
    originCity: DraftField;
    destinationCity: DraftField;
    hotelName: DraftField;
    note: DraftField;
  };
  items: Array<{
    type: 'transport';
    title: string;
    startAt: string;
    endAt: string;
    referenceCode: DraftField;
    source: 'ai_extracted';
    status: 'draft';
  }>;
  packingHints: Array<{
    label: string;
    checked: boolean;
    category: 'document' | 'electronics' | 'clothing' | 'medicine' | 'food' | 'other';
  }>;
  warnings: string[];
};

type AiImportJobRecord = {
  id: string;
  tripId: string | null;
  inputType: 'text';
  rawText: string;
  status: 'parsed' | 'committed';
  extractedPayloadJson: AiImportPayload;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
};

type CommitResult = {
  tripId: string;
  createdDayId: string;
  createdEventIds: string[];
  createdPackingItemIds: string[];
};

// Minimal DB types for writing imported records
type DbRecord = Record<string, unknown>;
type RawDatabase = { trips: DbRecord[] };

const backendRoot = path.resolve(fileURLToPath(new URL('../../', import.meta.url)));
const databasePath = () => path.resolve(backendRoot, appConfig.DATA_FILE_PATH);

const nowIso = () => new Date().toISOString();
const createId = (prefix: string) => `${prefix}_${randomUUID().slice(0, 8)}`;

async function readRawDatabase(): Promise<RawDatabase> {
  const dbPath = databasePath();
  await mkdir(path.dirname(dbPath), { recursive: true });
  try {
    const raw = await readFile(dbPath, 'utf-8');
    const parsed = JSON.parse(raw) as unknown;
    if (parsed && typeof parsed === 'object' && 'trips' in parsed && Array.isArray((parsed as RawDatabase).trips)) {
      return parsed as RawDatabase;
    }
    return { trips: [] };
  } catch {
    return { trips: [] };
  }
}

async function writeRawDatabase(db: RawDatabase) {
  const dbPath = databasePath();
  await mkdir(path.dirname(dbPath), { recursive: true });
  await writeFile(dbPath, JSON.stringify(db, null, 2), 'utf-8');
}

// ─── In-memory job store (jobs only live for server lifetime) ───────────────
const jobs = new Map<string, AiImportJobRecord>();
const commitResults = new Map<string, CommitResult>();

// ─── Text extraction ─────────────────────────────────────────────────────────

const buildFallbackDate = () => {
  const date = new Date();
  date.setDate(date.getDate() + 14);
  return `${date.getFullYear()}-${`${date.getMonth() + 1}`.padStart(2, '0')}-${`${date.getDate()}`.padStart(2, '0')}`;
};

const extractDate = (text: string): DraftField => {
  const explicit = text.match(/(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})/);
  if (explicit) {
    const [, year, month, day] = explicit;
    return { value: `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`, confidence: 'high' };
  }

  const partial = text.match(/(\d{1,2})月(\d{1,2})日/);
  if (partial) {
    const year = new Date().getFullYear();
    const [, month, day] = partial;
    return { value: `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`, confidence: 'medium' };
  }

  return { value: buildFallbackDate(), confidence: 'low' };
};

const extractTimes = (text: string) => {
  const matches = [...text.matchAll(/\b([01]?\d|2[0-3]):([0-5]\d)\b/g)].map((m) => m[0]);
  return {
    departureTime: { value: matches[0] ?? '09:30', confidence: matches[0] ? ('high' as const) : ('low' as const) },
    arrivalTime: { value: matches[1] ?? '11:45', confidence: matches[1] ? ('high' as const) : ('medium' as const) },
  };
};

const extractRoute = (text: string) => {
  const routeMatch = text.match(/([一-龥]{2,8})\s*(?:飞|到|->|→|-)\s*([一-龥]{2,8})/);
  if (routeMatch) {
    return {
      originCity: { value: routeMatch[1], confidence: 'high' as const },
      destinationCity: { value: routeMatch[2], confidence: 'high' as const },
    };
  }
  return {
    originCity: { value: '北京', confidence: 'low' as const },
    destinationCity: { value: '上海', confidence: 'low' as const },
  };
};

const extractPackingHints = (text: string) => {
  const candidates: Array<{ keyword: string; label: string; category: AiImportPayload['packingHints'][number]['category'] }> = [
    { keyword: '身份证', label: '身份证', category: 'document' },
    { keyword: '护照', label: '护照', category: 'document' },
    { keyword: '充电宝', label: '充电宝', category: 'electronics' },
    { keyword: '外套', label: '薄外套', category: 'clothing' },
  ];

  const matched = candidates.filter((item) => text.includes(item.keyword)).map((item) => ({ label: item.label, checked: true, category: item.category }));
  return matched.length
    ? matched
    : [
        { label: '身份证', checked: true, category: 'document' as const },
        { label: '充电宝', checked: true, category: 'electronics' as const },
        { label: '换洗衣物', checked: false, category: 'clothing' as const },
      ];
};

const parseRawText = (rawText: string): AiImportPayload => {
  const text = rawText.trim();
  const date = extractDate(text);
  const times = extractTimes(text);
  const route = extractRoute(text);
  const flightNo = text.match(/\b([A-Z]{2}\d{3,4})\b/i)?.[1]?.toUpperCase() ?? '待补充';
  const hotelMatch = text.match(/(?:入住|酒店|民宿)([^。\n]+)/);
  const note = text.includes('外滩') ? '周日晚上去外滩。' : '建议补充本次旅行的重点活动。';
  const warnings: string[] = [];

  if (flightNo === '待补充') warnings.push('没有识别到明确的航班号，建议人工确认交通班次。');
  if (date.confidence !== 'high') warnings.push('出发日期不是完整结构化信息，当前为推测值。');
  if (!hotelMatch) warnings.push('没有识别到明确酒店信息，commit 前建议补充。');

  return {
    tripDraft: {
      title: {
        value: `${route.destinationCity.value}行程草稿`,
        confidence: route.destinationCity.confidence === 'high' ? 'medium' : 'low',
      },
      startDate: date,
      endDate: date,
      originCity: route.originCity,
      destinationCity: route.destinationCity,
      hotelName: {
        value: hotelMatch ? hotelMatch[1].replace(/[，。,]/g, '').trim() : '',
        confidence: hotelMatch ? 'medium' : 'low',
      },
      note: { value: note, confidence: 'medium' },
    },
    items: [
      {
        type: 'transport',
        title: `${route.originCity.value} -> ${route.destinationCity.value}`,
        // Include Z so the stored datetime passes isoDateTimeSchema validation
        startAt: `${date.value}T${times.departureTime.value}:00.000Z`,
        endAt: `${date.value}T${times.arrivalTime.value}:00.000Z`,
        referenceCode: { value: flightNo, confidence: flightNo === '待补充' ? 'low' : 'high' },
        source: 'ai_extracted',
        status: 'draft',
      },
    ],
    packingHints: extractPackingHints(text),
    warnings,
  };
};

// ─── Route handlers ───────────────────────────────────────────────────────────

export async function registerAiImportRoutes(app: FastifyInstance) {
  app.post('/api/v1/ai-import-jobs', async (request, reply) => {
    const parsed = createJobBodySchema.parse(request.body);
    const timestamp = nowIso();
    const payload = parseRawText(parsed.rawText);

    const job: AiImportJobRecord = {
      id: randomUUID(),
      tripId: parsed.tripId ?? null,
      inputType: 'text',
      rawText: parsed.rawText,
      status: 'parsed',
      extractedPayloadJson: payload,
      errorMessage: null,
      createdAt: timestamp,
      updatedAt: timestamp,
    };

    jobs.set(job.id, job);
    return reply.code(201).send({ job });
  });

  app.get('/api/v1/ai-import-jobs/:jobId', async (request, reply) => {
    const { jobId } = jobParamsSchema.parse(request.params);
    const job = jobs.get(jobId);
    if (!job) return reply.code(404).send({ message: 'AI import job not found' });
    return { job };
  });

  app.post('/api/v1/ai-import-jobs/:jobId/commit', async (request, reply) => {
    const { jobId } = jobParamsSchema.parse(request.params);
    const job = jobs.get(jobId);
    if (!job) return reply.code(404).send({ message: 'AI import job not found' });

    // Idempotent: return existing commit result if already committed
    const existingCommit = commitResults.get(jobId);
    if (existingCommit) {
      return { job, commit: existingCommit, idempotent: true };
    }

    const timestamp = nowIso();
    const payload = job.extractedPayloadJson;
    const draft = payload.tripDraft;

    const tripId = createId('trip');
    const dayId = createId('day');
    const eventIds = payload.items.map(() => createId('event'));
    const packingIds = payload.packingHints.map(() => createId('packing'));

    // Build the new trip record to write into the JSON database
    const newTrip: DbRecord = {
      id: tripId,
      title: draft.title.value,
      status: 'planning',
      startDate: draft.startDate.value,
      endDate: draft.endDate.value || draft.startDate.value,
      originCity: draft.originCity.value,
      destinationCity: draft.destinationCity.value,
      primaryTransportMode: 'flight',
      hotelName: draft.hotelName.value,
      note: draft.note.value,
      countdownAnchorAt: payload.items[0]?.startAt ?? `${draft.startDate.value}T09:00:00.000Z`,
      createdVia: 'ai_import',
      days: [
        {
          id: dayId,
          date: draft.startDate.value,
          summary: 'AI 导入行程',
          hint: '由文本提取生成，可在日历页继续补充。',
          highlightTag: '待确认',
          sortOrder: 0,
          createdAt: timestamp,
          updatedAt: timestamp,
        },
      ],
      events: payload.items.map((item, index) => ({
        id: eventIds[index],
        tripDayId: dayId,
        eventType: 'transport',
        title: item.title,
        description: '',
        startAt: item.startAt,
        endAt: item.endAt,
        transportMode: 'flight',
        referenceCode: item.referenceCode.value || undefined,
        source: 'ai_import',
        status: 'draft',
        createdAt: timestamp,
        updatedAt: timestamp,
      })),
      packingItems: payload.packingHints.map((hint, index) => ({
        id: packingIds[index],
        label: hint.label,
        checked: hint.checked,
        category: hint.category,
        source: 'ai_generated',
        sortOrder: index,
        createdAt: timestamp,
        updatedAt: timestamp,
      })),
      createdAt: timestamp,
      updatedAt: timestamp,
    };

    const db = await readRawDatabase();
    db.trips.push(newTrip);
    await writeRawDatabase(db);

    const commit: CommitResult = {
      tripId,
      createdDayId: dayId,
      createdEventIds: eventIds,
      createdPackingItemIds: packingIds,
    };

    const nextJob: AiImportJobRecord = { ...job, tripId, status: 'committed', updatedAt: timestamp };
    jobs.set(jobId, nextJob);
    commitResults.set(jobId, commit);

    return reply.code(201).send({ job: nextJob, commit, idempotent: false });
  });
}
