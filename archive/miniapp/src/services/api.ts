type RequestMethod = NonNullable<UniApp.RequestOptions["method"]>;
type ApiMethod = "GET" | "POST" | "PATCH" | "DELETE";

type ApiRequestOptions = {
  method?: ApiMethod;
  data?: unknown;
  headers?: Record<string, string>;
};

type ApiErrorPayload = {
  message?: string;
  error?: string;
};

type HomeOverviewResponse = {
  upcomingTrips: Array<{
    id: string;
    title: string;
    destinationCity: string;
    startDate: string;
    endDate: string;
    status: string;
    primaryTransportMode: string;
  }>;
  stats: {
    plannedCities: number;
    tripCount: number;
    confirmedTripCount: number;
  };
};

type TripDayRecord = {
  id: string;
  date: string;
  summary: string;
  hint: string;
  highlightTag: string;
  sortOrder: number;
  createdAt?: string;
  updatedAt?: string;
};

type TripEventRecord = {
  id: string;
  tripDayId?: string;
  eventType: string;
  title: string;
  description: string;
  startAt: string;
  endAt?: string;
  locationName?: string;
  address?: string;
  transportMode?: string;
  referenceCode?: string;
  source: string;
  status: string;
  meta?: Record<string, string>;
  createdAt?: string;
  updatedAt?: string;
};

type PackingItemRecord = {
  id: string;
  label: string;
  checked: boolean;
  category: string;
  source: string;
  sortOrder: number;
  createdAt?: string;
  updatedAt?: string;
};

type TripRecord = {
  id: string;
  title: string;
  status: string;
  startDate: string;
  endDate: string;
  originCity: string;
  destinationCity: string;
  primaryTransportMode: string;
  hotelName: string;
  note: string;
  countdownAnchorAt: string;
  createdVia: string;
  coverImageUrl?: string;
  days: TripDayRecord[];
  events: TripEventRecord[];
  packingItems: PackingItemRecord[];
  createdAt: string;
  updatedAt: string;
};

type TripListResponse = {
  items: TripRecord[];
};

type TripItemResponse = {
  item: TripRecord;
};

type TripCalendarResponse = {
  tripId: string;
  trip: {
    id: string;
    title: string;
    status: string;
    startDate: string;
    endDate: string;
    destinationCity: string;
  };
  days: TripDayRecord[];
  events: TripEventRecord[];
};

type TripDayDetailsResponse = {
  tripId: string;
  day: TripDayRecord;
  events: TripEventRecord[];
};

type PackingItemsResponse = {
  tripId: string;
  items: PackingItemRecord[];
};

type AiImportDraftField = {
  value: string;
  confidence: "high" | "medium" | "low";
};

type AiImportJob = {
  id: string;
  tripId: string | null;
  inputType: "text";
  rawText: string;
  status: "parsed" | "committed";
  extractedPayloadJson: {
    tripDraft: {
      title: AiImportDraftField;
      startDate: AiImportDraftField;
      endDate: AiImportDraftField;
      originCity: AiImportDraftField;
      destinationCity: AiImportDraftField;
      hotelName: AiImportDraftField;
      note: AiImportDraftField;
    };
    items: Array<{
      type: "transport";
      title: string;
      startAt: string;
      endAt: string;
      referenceCode: AiImportDraftField;
      source: "ai_extracted";
      status: "draft";
    }>;
    packingHints: Array<{
      label: string;
      checked: boolean;
      category: string;
    }>;
    warnings: string[];
  };
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
};

type AiImportJobResponse = {
  job: AiImportJob;
};

type AiImportCommitResponse = {
  job: AiImportJob;
  commit: {
    tripId: string;
    createdDayId: string;
    createdEventIds: string[];
    createdPackingItemIds: string[];
  };
  idempotent: boolean;
};

const DEFAULT_API_BASE_URL = "https://www.willer.tech/api/v1";

const trimTrailingSlash = (value: string) => value.replace(/\/+$/, "");
const trimLeadingSlash = (value: string) => value.replace(/^\/+/, "");

export const apiBaseUrl = trimTrailingSlash(import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL);

export class ApiRequestError extends Error {
  statusCode: number;
  data?: unknown;

  constructor(message: string, statusCode: number, data?: unknown) {
    super(message);
    this.name = "ApiRequestError";
    this.statusCode = statusCode;
    this.data = data;
  }
}

const buildUrl = (path: string) => {
  const normalizedPath = trimLeadingSlash(path);
  return `${apiBaseUrl}/${normalizedPath}`;
};

const extractErrorMessage = (data: unknown) => {
  if (!data || typeof data !== "object") return "";
  const payload = data as ApiErrorPayload;
  return payload.message || payload.error || "";
};

export const apiRequest = <T>(path: string, options: ApiRequestOptions = {}) =>
  new Promise<T>((resolve, reject) => {
    const url = buildUrl(path);
    const method = options.method || "GET";

    uni.request({
      url,
      method: method as RequestMethod,
      data: options.data as UniApp.RequestOptions["data"],
      header: {
        "content-type": "application/json",
        ...(options.headers || {}),
      },
      success: (response) => {
        const statusCode = response.statusCode;
        const data = response.data;

        if (statusCode >= 200 && statusCode < 300) {
          resolve(data as T);
          return;
        }

        reject(new ApiRequestError(extractErrorMessage(data) || `Request failed with status ${statusCode}`, statusCode, data));
      },
      fail: (error) => {
        reject(new ApiRequestError(error.errMsg || "Network request failed", 0, error));
      },
    });
  });

export const homeApi = {
  getOverview: () => apiRequest<HomeOverviewResponse>("home"),
};

export const tripApi = {
  list: () => apiRequest<TripListResponse>("trips"),
  create: (data: {
    title: string;
    startDate: string;
    endDate: string;
    originCity?: string;
    destinationCity?: string;
    primaryTransportMode?: string;
    hotelName?: string;
    note?: string;
    countdownAnchorAt?: string;
    createdVia?: string;
  }) => apiRequest<TripItemResponse>("trips", { method: "POST", data }),
  get: (tripId: string) => apiRequest<TripItemResponse>(`trips/${tripId}`),
  update: (tripId: string, data: Partial<Omit<TripRecord, "id" | "days" | "events" | "packingItems" | "createdAt" | "updatedAt">>) =>
    apiRequest<TripItemResponse>(`trips/${tripId}`, { method: "PATCH", data }),
  getCalendar: (tripId: string, month?: string) =>
    apiRequest<TripCalendarResponse>(month ? `trips/${tripId}/calendar?month=${encodeURIComponent(month)}` : `trips/${tripId}/calendar`),
  getDay: (tripId: string, date: string) => apiRequest<TripDayDetailsResponse>(`trips/${tripId}/days/${date}`),
  createDay: (
    tripId: string,
    data: {
      date: string;
      summary?: string;
      hint?: string;
      highlightTag?: string;
      sortOrder?: number;
    },
  ) => apiRequest<TripItemResponse>(`trips/${tripId}/days`, { method: "POST", data }),
  updateDay: (
    tripId: string,
    dayId: string,
    data: Partial<{
      date: string;
      summary: string;
      hint: string;
      highlightTag: string;
      sortOrder: number;
    }>,
  ) => apiRequest<TripItemResponse>(`trips/${tripId}/days/${dayId}`, { method: "PATCH", data }),
  deleteDay: (tripId: string, dayId: string) => apiRequest<TripItemResponse>(`trips/${tripId}/days/${dayId}`, { method: "DELETE" }),
  createEvent: (
    tripId: string,
    data: {
      tripDayId?: string;
      eventType: string;
      title: string;
      description?: string;
      startAt: string;
      endAt?: string;
      locationName?: string;
      address?: string;
      transportMode?: string;
      referenceCode?: string;
      source?: string;
      status?: string;
      meta?: Record<string, string>;
    },
  ) => apiRequest<TripItemResponse>(`trips/${tripId}/events`, { method: "POST", data }),
  updateEvent: (
    eventId: string,
    data: Partial<{
      tripDayId: string;
      eventType: string;
      title: string;
      description: string;
      startAt: string;
      endAt: string;
      locationName: string;
      address: string;
      transportMode: string;
      referenceCode: string;
      source: string;
      status: string;
      meta: Record<string, string>;
    }>,
  ) => apiRequest<TripItemResponse>(`events/${eventId}`, { method: "PATCH", data }),
  deleteEvent: (eventId: string) => apiRequest<TripItemResponse>(`events/${eventId}`, { method: "DELETE" }),
  listPackingItems: (tripId: string) => apiRequest<PackingItemsResponse>(`trips/${tripId}/packing-items`),
  createPackingItem: (
    tripId: string,
    data: {
      label: string;
      checked?: boolean;
      category?: string;
      source?: string;
      sortOrder?: number;
    },
  ) => apiRequest<TripItemResponse>(`trips/${tripId}/packing-items`, { method: "POST", data }),
  updatePackingItem: (
    itemId: string,
    data: Partial<{
      label: string;
      checked: boolean;
      category: string;
      source: string;
      sortOrder: number;
    }>,
  ) => apiRequest<TripItemResponse>(`packing-items/${itemId}`, { method: "PATCH", data }),
  deletePackingItem: (itemId: string) => apiRequest<TripItemResponse>(`packing-items/${itemId}`, { method: "DELETE" }),
};

export const aiImportApi = {
  createJob: (data: { inputType?: "text"; rawText: string; tripId?: string }) =>
    apiRequest<AiImportJobResponse>("ai-import-jobs", { method: "POST", data }),
  getJob: (jobId: string) => apiRequest<AiImportJobResponse>(`ai-import-jobs/${jobId}`),
  commitJob: (jobId: string, data: Record<string, never> = {}) =>
    apiRequest<AiImportCommitResponse>(`ai-import-jobs/${jobId}/commit`, { method: "POST", data }),
};

export type {
  AiImportCommitResponse,
  AiImportJob,
  AiImportJobResponse,
  HomeOverviewResponse,
  PackingItemRecord,
  PackingItemsResponse,
  TripCalendarResponse,
  TripDayDetailsResponse,
  TripDayRecord,
  TripEventRecord,
  TripItemResponse,
  TripListResponse,
  TripRecord,
};
