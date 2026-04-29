import { randomUUID } from 'node:crypto';
import { z } from 'zod';
import type { FastifyInstance } from 'fastify';

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

const jobs = new Map<string, AiImportJobRecord>();
const commitResults = new Map<string, CommitResult>();

const buildFallbackDate = () => {
  const date = new Date();
  date.setDate(date.getDate() + 14);

  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');

  return `${year}-${month}-${day}`;
};

const extractDate = (text: string): DraftField => {
  const explicit = text.match(/(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})/);
  if (explicit) {
    const [, year, month, day] = explicit;
    return {
      value: `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`,
      confidence: 'high',
    };
  }

  const partial = text.match(/(\d{1,2})月(\d{1,2})日/);
  if (partial) {
    const year = new Date().getFullYear();
    const [, month, day] = partial;
    return {
      value: `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`,
      confidence: 'medium',
    };
  }

  return {
    value: buildFallbackDate(),
    confidence: 'low',
  };
};

const extractTimes = (text: string) => {
  const matches = [...text.matchAll(/\b([01]?\d|2[0-3]):([0-5]\d)\b/g)].map((match) => match[0]);

  return {
    departureTime: {
      value: matches[0] ?? '09:30',
      confidence: matches[0] ? ('high' as const) : ('low' as const),
    },
    arrivalTime: {
      value: matches[1] ?? '11:45',
      confidence: matches[1] ? ('high' as const) : ('medium' as const),
    },
  };
};

const extractRoute = (text: string) => {
  const routeMatch = text.match(/([\u4e00-\u9fa5]{2,8})\s*(?:飞|到|->|→|-)\s*([\u4e00-\u9fa5]{2,8})/);
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

  const matched = candidates
    .filter((item) => text.includes(item.keyword))
    .map((item) => ({
      label: item.label,
      checked: true,
      category: item.category,
    }));

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

  if (flightNo === '待补充') {
    warnings.push('没有识别到明确的航班号，建议人工确认交通班次。');
  }

  if (date.confidence !== 'high') {
    warnings.push('出发日期不是完整结构化信息，当前为推测值。');
  }

  if (!hotelMatch) {
    warnings.push('没有识别到明确酒店信息，commit 前建议补充。');
  }

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
      note: {
        value: note,
        confidence: 'medium',
      },
    },
    items: [
      {
        type: 'transport',
        title: `${route.originCity.value} -> ${route.destinationCity.value}`,
        startAt: `${date.value}T${times.departureTime.value}:00`,
        endAt: `${date.value}T${times.arrivalTime.value}:00`,
        referenceCode: {
          value: flightNo,
          confidence: flightNo === '待补充' ? 'low' : 'high',
        },
        source: 'ai_extracted',
        status: 'draft',
      },
    ],
    packingHints: extractPackingHints(text),
    warnings,
  };
};

export async function registerAiImportRoutes(app: FastifyInstance) {
  app.post('/api/v1/ai-import-jobs', async (request, reply) => {
    const parsed = createJobBodySchema.parse(request.body);
    const timestamp = new Date().toISOString();
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

    if (!job) {
      return reply.code(404).send({
        message: 'AI import job not found',
      });
    }

    return { job };
  });

  app.post('/api/v1/ai-import-jobs/:jobId/commit', async (request, reply) => {
    const { jobId } = jobParamsSchema.parse(request.params);
    const job = jobs.get(jobId);

    if (!job) {
      return reply.code(404).send({
        message: 'AI import job not found',
      });
    }

    const existingCommit = commitResults.get(jobId);
    if (existingCommit) {
      return {
        job,
        commit: existingCommit,
        idempotent: true,
      };
    }

    const timestamp = new Date().toISOString();
    const commit: CommitResult = {
      tripId: job.tripId ?? `trip_${job.id.slice(0, 8)}`,
      createdDayId: `day_${job.id.slice(0, 8)}`,
      createdEventIds: job.extractedPayloadJson.items.map(() => `event_${randomUUID().slice(0, 8)}`),
      createdPackingItemIds: job.extractedPayloadJson.packingHints.map(() => `packing_${randomUUID().slice(0, 8)}`),
    };

    const nextJob: AiImportJobRecord = {
      ...job,
      status: 'committed',
      updatedAt: timestamp,
    };

    jobs.set(jobId, nextJob);
    commitResults.set(jobId, commit);

    return {
      job: nextJob,
      commit,
      idempotent: false,
    };
  });
}
