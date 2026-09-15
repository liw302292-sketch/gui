/** 统一 API 客户端。
 *
 * 前端只访问同源 /api/backend/*，由 Next rewrites 代理到 FastAPI，
 * JWT 存放在 HttpOnly Cookie 中，前端代码永远拿不到、也不需要拿到 token。
 */

import type {
  AdminDashboard,
  AiUsage,
  ApiEnvelope,
  Category,
  Customer,
  DashboardData,
  Followup,
  IndustryTemplateSummary,
  MeResponse,
  Plan,
  PriceRule,
  Product,
  PublicQuotePayload,
  Quote,
  QuoteListItem,
  QuoteTemplate,
  Requirement,
} from "./types";

export const API_BASE = "/api/backend";

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(message: string, status: number, code = "error", details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

const FRIENDLY_FALLBACK = "网络不稳定，请稍后重试。";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...(init.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(FRIENDLY_FALLBACK, 0, "network_error");
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    if (response.ok) return undefined as T;
    throw new ApiError(FRIENDLY_FALLBACK, response.status, "unexpected_response");
  }

  const payload = (await response.json()) as ApiEnvelope<T> & { message?: string; code?: string; details?: unknown };
  if (!response.ok) {
    throw new ApiError(
      payload?.message || FRIENDLY_FALLBACK,
      response.status,
      payload?.code ?? "error",
      payload?.details,
    );
  }
  return payload.data as T;
}

function query(params?: Record<string, string | number | boolean | null | undefined>): string {
  if (!params) return "";
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") search.set(key, String(value));
  });
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const api = {
  get: <T>(path: string, params?: Record<string, string | number | boolean | null | undefined>) =>
    request<T>(`${path}${query(params)}`),
  post: <T>(path: string, body?: unknown, params?: Record<string, string | number | boolean | null | undefined>) =>
    request<T>(`${path}${query(params)}`, {
      method: "POST",
      body: body instanceof FormData ? body : body === undefined ? undefined : JSON.stringify(body),
    }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body === undefined ? undefined : JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  postForm: <T>(path: string, form: FormData) => request<T>(path, { method: "POST", body: form }),
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message || FRIENDLY_FALLBACK;
  return FRIENDLY_FALLBACK;
}

/* ------------------------------------------------------------------ */
/* 业务接口封装                                                        */
/* ------------------------------------------------------------------ */

export const authApi = {
  me: () => api.get<MeResponse>("/auth/me"),
  login: (identifier: string, password: string, remember = true) =>
    api.post<{ access_token: string; must_change_password: boolean }>("/auth/login", {
      identifier,
      password,
      remember,
    }),
  register: (payload: {
    email?: string;
    phone?: string;
    password: string;
    name?: string;
    company_name?: string;
    industry_id?: string;
  }) => api.post<{ company: { id: number; name: string } }>("/auth/register", payload),
  logout: () => api.post<unknown>("/auth/logout"),
  changePassword: (old_password: string, new_password: string) =>
    api.post<unknown>("/auth/change-password", { old_password, new_password }),
  checkAvailability: (params: { email?: string; phone?: string }) =>
    api.get<{ email_available: boolean; phone_available: boolean }>("/auth/check-availability", params),
};

export const companyApi = {
  detail: () => api.get<Record<string, unknown>>("/company"),
  update: (payload: Record<string, unknown>) => api.put<Record<string, unknown>>("/company", payload),
  dashboard: () => api.get<DashboardData>("/company/dashboard"),
  analytics: (period: "day" | "week" | "month") =>
    api.get<{
      period: string;
      quote_count: number;
      quote_amount: number;
      won_count: number;
      won_amount: number;
      conversion_rate: number;
      average_quote_amount: number;
      average_margin: number;
      followup_count: number;
      new_customers: number;
      by_category: { category: string; count: number; amount: number }[];
      status_breakdown: { status: string; label: string; count: number }[];
    }>("/company/analytics", { period }),
  industries: () => api.get<IndustryTemplateSummary[]>("/company/industries"),
  notifications: () =>
    api.get<{
      items: {
        id: number;
        type: string;
        title: string;
        content: string | null;
        link: string | null;
        is_read: boolean;
        created_at: string | null;
      }[];
      unread: number;
    }>("/company/notifications"),
  readNotifications: (notification_id?: number) =>
    api.post<unknown>("/company/notifications/read", undefined, { notification_id }),
  search: (q: string) =>
    api.get<{
      customers: { id: number; name: string; contact_name: string | null; phone: string | null }[];
      quotes: { id: number; quote_no: string; project_name: string; total_amount: number; status: string }[];
    }>("/company/search", { q }),
};

export const productApi = {
  list: (params?: Record<string, string | number | boolean | null | undefined>) =>
    api.get<{ items: Product[]; total: number; page: number; page_size: number }>("/products", params),
  detail: (id: number) => api.get<Product>(`/products/${id}`),
  create: (payload: Record<string, unknown>) => api.post<Product>("/products", payload),
  update: (id: number, payload: Record<string, unknown>) => api.put<Product>(`/products/${id}`, payload),
  remove: (id: number) => api.del<unknown>(`/products/${id}`),
  categories: () => api.get<Category[]>("/products/categories"),
  createCategory: (payload: Record<string, unknown>) => api.post<{ id: number }>("/products/categories", payload),
  updateCategory: (id: number, payload: Record<string, unknown>) =>
    api.put<unknown>(`/products/categories/${id}`, payload),
  removeCategory: (id: number) => api.del<unknown>(`/products/categories/${id}`),
  importFile: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.postForm<{ created: number; updated: number; skipped: number }>("/products/import", form);
  },
  importTemplate: () =>
    api.get<{ columns: string[]; example: Record<string, string | number> }>("/products/template/download"),
};

export const priceRuleApi = {
  list: () => api.get<PriceRule[]>("/price-rules"),
  types: () => api.get<{ value: string; label: string; formula: string }[]>("/price-rules/types"),
  create: (payload: Record<string, unknown>) => api.post<PriceRule>("/price-rules", payload),
  update: (id: number, payload: Record<string, unknown>) => api.put<PriceRule>(`/price-rules/${id}`, payload),
  remove: (id: number) => api.del<unknown>(`/price-rules/${id}`),
};

export const quoteApi = {
  list: (params?: Record<string, string | number | boolean | null | undefined>) =>
    api.get<{
      items: QuoteListItem[];
      total: number;
      page: number;
      page_size: number;
      summary: {
        quote_count: number;
        quote_amount: number;
        total_cost: number;
        won_count: number;
        won_amount: number;
      };
    }>("/quotes", params),
  detail: (id: number) => api.get<Quote>(`/quotes/${id}`),
  create: (payload: Record<string, unknown>) => api.post<Quote>("/quotes", payload),
  update: (id: number, payload: Record<string, unknown>) => api.put<Quote>(`/quotes/${id}`, payload),
  recalculate: (id: number, payload: Record<string, unknown>) =>
    api.post<Quote>(`/quotes/${id}/recalculate`, payload),
  send: (id: number, payload: { valid_days?: number; password?: string | null }) =>
    api.post<{ public_token: string; public_url: string; expires_at: string | null; requires_password: boolean }>(
      `/quotes/${id}/send`,
      payload,
    ),
  setStatus: (id: number, status: string, note?: string) =>
    api.post<Quote>(`/quotes/${id}/status`, { status, note }),
  versions: (id: number) =>
    api.get<{
      versions: {
        id: number;
        version_no: number;
        total_amount: number;
        gross_margin: number;
        change_note: string | null;
        created_at: string | null;
      }[];
      latest_snapshot: Record<string, unknown>;
    }>(`/quotes/${id}/versions`),
  audit: (id: number) =>
    api.get<
      {
        id: number;
        action: string;
        user_name: string | null;
        summary: string | null;
        before: Record<string, unknown>;
        after: Record<string, unknown>;
        created_at: string | null;
      }[]
    >(`/quotes/${id}/audit`),
  remove: (id: number) => api.del<unknown>(`/quotes/${id}`),
  pdfUrl: (id: number) => `${API_BASE}/quotes/${id}/pdf`,
};

export const quoteTemplateApi = {
  list: () => api.get<QuoteTemplate[]>("/quote-templates"),
  create: (payload: Record<string, unknown>) => api.post<QuoteTemplate>("/quote-templates", payload),
  update: (id: number, payload: Record<string, unknown>) =>
    api.put<QuoteTemplate>(`/quote-templates/${id}`, payload),
  remove: (id: number) => api.del<unknown>(`/quote-templates/${id}`),
};

export const customerApi = {
  list: (params?: Record<string, string | number | boolean | null | undefined>) =>
    api.get<{
      items: Customer[];
      total: number;
      page: number;
      page_size: number;
      summary: { total_customers: number; total_amount: number };
    }>("/customers", params),
  detail: (id: number) =>
    api.get<{
      customer: Customer;
      quotes: {
        id: number;
        quote_no: string;
        project_name: string;
        status: string;
        status_label: string;
        total_amount: number;
        view_count: number;
        created_at: string | null;
      }[];
      followups: Followup[];
      activities: { type: string; title: string; detail: string | null; status: string; at: string | null }[];
    }>(`/customers/${id}`),
  create: (payload: Record<string, unknown>) => api.post<Customer>("/customers", payload),
  update: (id: number, payload: Record<string, unknown>) => api.put<Customer>(`/customers/${id}`, payload),
  remove: (id: number) => api.del<unknown>(`/customers/${id}`),
  removeMany: (ids: number[]) => Promise.all(ids.map((id) => api.del<unknown>(`/customers/${id}`))),
  statuses: () => api.get<{ value: string; label: string; color: string }[]>("/customers/statuses"),
};

export const followupApi = {
  list: (params?: Record<string, string | number | boolean | null | undefined>) =>
    api.get<{ items: Followup[]; total: number; page: number; page_size: number }>("/followups", params),
  today: () =>
    api.get<{
      count: number;
      hint: string;
      items: {
        id: number;
        name: string;
        contact_name: string | null;
        phone: string | null;
        status: string;
        next_followup_at: string | null;
        total_amount: number;
      }[];
    }>("/followups/today"),
  create: (payload: Record<string, unknown>) => api.post<Followup>("/followups", payload),
  update: (id: number, payload: Record<string, unknown>) => api.put<Followup>(`/followups/${id}`, payload),
  remove: (id: number) => api.del<unknown>(`/followups/${id}`),
};

export const aiApi = {
  status: () =>
    api.get<{
      mode: string;
      models: { text: string; reasoning: string; vision: string };
      base_url: string;
      usage: AiUsage;
    }>("/ai/status"),
  test: () => api.post<{ mode: string; ok: boolean; message: string }>("/ai/test"),
  extract: (form: FormData) =>
    api.postForm<{
      mode: string;
      model: string;
      file_id: number | null;
      requirement: Requirement;
      usage: AiUsage;
    }>("/ai/extract", form),
  extractText: (text: string) =>
    api.post<{ requirement: Requirement; usage: AiUsage }>("/ai/extract-text", { text }),
  missingFields: (requirement: Record<string, unknown>) =>
    api.post<{ result: { questions: { field: string; question: string; impact: string }[]; summary: string } }>(
      "/ai/missing-fields",
      { requirement },
    ),
  reply: (requirement: Record<string, unknown>, quote: Record<string, unknown>, style: string) =>
    api.post<{ result: { style: string; content: string; follow_up_suggestion: string } }>("/ai/reply", {
      requirement,
      quote,
      style,
    }),
  explain: (quote: Record<string, unknown>, question: string) =>
    api.post<{ result: { reasons: string[]; customer_reply: string; adjust_options: string[] } }>("/ai/explain", {
      quote,
      question,
    }),
  suggestPrice: (requirement: Record<string, unknown>, category?: string | null) =>
    api.post<{
      result: {
        range_low: number | null;
        range_high: number | null;
        unit_suggestion: string;
        basis: string;
        sample_size: number;
        confidence: number;
        caution: string;
        history?: { sample_size: number; average_amount: number; min_amount: number; max_amount: number };
      };
    }>("/ai/suggest-price", { requirement, category }),
  usage: () =>
    api.get<{
      summary: AiUsage;
      recent_tasks: {
        id: number;
        task_type: string;
        status: string;
        model: string;
        mode: string;
        input_tokens: number;
        output_tokens: number;
        estimated_cost: number;
        latency_ms: number;
        confidence: number | null;
        error: string | null;
        created_at: string | null;
      }[];
    }>("/ai/usage"),
};

export const fileApi = {
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.postForm<{ id: number; name: string; kind: string; size: number; url: string }>(
      "/files/upload",
      form,
    );
  },
  url: (id: number) => `${API_BASE}/files/${id}`,
  storage: () =>
    api.get<{ backend: string; used_bytes: number; used_mb: number; quota_mb: number; usage_ratio: number }>(
      "/files/storage/info",
    ),
};

export const billingApi = {
  plans: (includeHidden = false) => api.get<{ items: Plan[]; feature_labels: Record<string, string> }>(
    "/subscription/plans",
    { include_hidden: includeHidden },
  ),
  current: () =>
    api.get<{
      plan: Plan | null;
      subscription: { status: string; start_at: string | null; end_at: string | null; auto_renew: boolean };
      ai_usage: AiUsage;
    }>("/subscription/current"),
  orders: () =>
    api.get<
      {
        id: number;
        order_no: string;
        plan_code: string;
        amount: number;
        payment_method: string;
        status: string;
        paid_at: string | null;
        created_at: string | null;
        remark: string | null;
      }[]
    >("/subscription/orders"),
  createOrder: (plan_code: string, payment_method?: string) =>
    api.post<{ id: number; order_no: string; amount: number; status: string; payment_method: string }>(
      "/subscription/orders",
      undefined,
      { plan_code, payment_method },
    ),
  cancelAutoRenew: () => api.post<unknown>("/subscription/cancel"),
};

export const adminApi = {
  dashboard: () => api.get<AdminDashboard>("/admin/dashboard"),
  companies: (params?: Record<string, string | number | boolean | null | undefined>) =>
    api.get<{
      items: {
        id: number;
        name: string;
        industry_id: string;
        status: string;
        plan_code: string | null;
        plan_name: string | null;
        owner_name: string | null;
        owner_email: string | null;
        owner_phone: string | null;
        member_count: number;
        quote_count: number;
        ai_calls: number;
        created_at: string | null;
      }[];
      total: number;
      page: number;
      page_size: number;
    }>("/admin/companies", params),
  companyDetail: (id: number) =>
    api.get<{
      company: Record<string, unknown>;
      members: { id: number; name: string; email: string | null; phone: string | null; role: string }[];
      ai_usage: AiUsage;
      quote_count: number;
      customer_count: number;
    }>(`/admin/companies/${id}`),
  setCompanyStatus: (id: number, status: string, reason?: string) =>
    api.post<unknown>(`/admin/companies/${id}/status`, { status, reason }),
  setQuota: (id: number, quota: number) =>
    api.post<unknown>(`/admin/companies/${id}/quota`, undefined, { ai_monthly_quota: quota }),
  users: (params?: Record<string, string | number | boolean | null | undefined>) =>
    api.get<{
      items: {
        id: number;
        name: string;
        email: string | null;
        phone: string | null;
        is_superadmin: boolean;
        status: string;
        company_count: number;
        last_login_at: string | null;
        created_at: string | null;
      }[];
      total: number;
    }>("/admin/users", params),
  setUserStatus: (id: number, status: string) => api.post<unknown>(`/admin/users/${id}/status`, undefined, { status }),
  plans: () => api.get<Plan[]>("/admin/plans"),
  createPlan: (payload: Record<string, unknown>) => api.post<Plan>("/admin/plans", payload),
  updatePlan: (id: number, payload: Record<string, unknown>) => api.put<Plan>(`/admin/plans/${id}`, payload),
  orders: () =>
    api.get<
      {
        id: number;
        order_no: string;
        company_name: string | null;
        plan_code: string;
        amount: number;
        payment_method: string;
        status: string;
        paid_at: string | null;
        created_at: string | null;
      }[]
    >("/admin/orders"),
  subscriptions: () =>
    api.get<
      {
        id: number;
        company_name: string | null;
        plan_code: string | null;
        status: string;
        start_at: string | null;
        end_at: string | null;
        auto_renew: boolean;
      }[]
    >("/admin/subscriptions"),
  aiUsage: (days = 30) =>
    api.get<{
      total_calls: number;
      today_calls: number;
      total_cost: number;
      today_cost: number;
      by_model: { model: string; calls: number; cost: number }[];
      by_company: { company_id: number; company_name: string; calls: number; cost: number }[];
      by_task: { task_type: string; calls: number }[];
    }>("/admin/ai/usage", { days }),
  aiTasks: (status?: string) =>
    api.get<
      {
        id: number;
        company_id: number;
        task_type: string;
        status: string;
        model: string;
        mode: string;
        input_tokens: number;
        output_tokens: number;
        estimated_cost: number;
        latency_ms: number;
        error: string | null;
        created_at: string | null;
      }[]
    >("/admin/ai/tasks", { status }),
  quoteStats: () =>
    api.get<{
      quote_count: number;
      quote_amount: number;
      total_cost: number;
      by_status: { status: string; count: number; amount: number }[];
      top_companies: { company_id: number; company_name: string; count: number; amount: number }[];
    }>("/admin/quotes/stats"),
  logs: (level?: string) =>
    api.get<{
      application_logs: { time: string; level: string; logger: string; message: string }[];
      audit_logs: {
        id: number;
        company_id: number | null;
        user_name: string | null;
        action: string;
        target_type: string;
        target_id: number | null;
        summary: string | null;
        created_at: string | null;
      }[];
    }>("/admin/logs", { level }),
  errors: () =>
    api.get<{
      ai_failures: {
        id: number;
        company_id: number;
        task_type: string;
        model: string;
        error: string | null;
        raw_response: string;
        created_at: string | null;
      }[];
      error_logs: { time: string; level: string; logger: string; message: string }[];
    }>("/admin/errors"),
  settings: () =>
    api.get<{
      runtime: Record<string, string | number>;
      stored: Record<string, unknown>;
      industries: IndustryTemplateSummary[];
      prompt_files: { name: string; size: number }[];
    }>("/admin/settings"),
  saveSetting: (key: string, value: Record<string, unknown>, description?: string) =>
    api.put<unknown>("/admin/settings", { key, value, description }),
};

export const publicApi = {
  view: (token: string, password?: string) =>
    api.get<PublicQuotePayload>(`/quote-public/${token}`, {
      password,
      track: true,
    }),
  accept: (token: string) => api.post<unknown>(`/quote-public/${token}/accept`),
  pdfUrl: (token: string, password?: string) =>
    `${API_BASE}/quote-public/${token}/pdf${password ? `?password=${encodeURIComponent(password)}` : ""}`,
};

export const metaApi = {
  meta: () =>
    api.get<{
      app_name: string;
      industries: IndustryTemplateSummary[];
      ai_mode: string;
      pricing_modes: { value: string; label: string }[];
      quote_statuses: { value: string; label: string }[];
      units: string[];
    }>("/meta"),
  health: () => api.get<{ ok: boolean; status: string }>("/health"),
};

