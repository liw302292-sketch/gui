/** 与后端 API 对应的类型定义。 */

export type QuoteStatus = "draft" | "sent" | "viewed" | "following" | "won" | "void";
export type CustomerStatus = "new" | "quoted" | "communicating" | "high_intent" | "won" | "lost";
export type PlanLevel = "economy" | "standard" | "premium";

export interface ApiEnvelope<T> {
  ok: boolean;
  message?: string;
  data: T;
}

export interface UserProfile {
  id: number;
  email: string | null;
  phone: string | null;
  name: string;
  is_superadmin: boolean;
  must_change_password: boolean;
  created_at?: string | null;
}

export interface CompanyBrief {
  id: number;
  name: string;
  industry_id: string;
  role: string;
  plan_code: string | null;
  plan_name: string | null;
  ai_quota: number;
  logo_file_id: number | null;
}

export interface MeResponse {
  user: UserProfile;
  company: CompanyBrief | null;
  unread_notifications: number;
}

export interface RequirementItem {
  category?: string | null;
  product_name: string;
  spec?: string | null;
  unit: string;
  quantity: number;
  width?: number | null;
  height?: number | null;
  depth?: number | null;
  weight?: number | null;
  material?: string | null;
  process?: string[];
  installation?: boolean | null;
  remark?: string | null;
  unit_price?: number | null;
  cost_price?: number | null;
  match_confidence?: number | null;
}

export interface MissingQuestion {
  field: string;
  question: string;
  impact: "high" | "medium" | "low" | string;
}

export interface Requirement {
  project_name?: string | null;
  customer_name?: string | null;
  items: RequirementItem[];
  transport_required?: boolean | null;
  installation_required?: boolean | null;
  installation_location?: string | null;
  deadline?: string | null;
  missing_fields: string[];
  unknown_fields?: string[];
  inference?: { notes?: string };
  confidence: number;
  mode?: string;
  model?: string;
  missing_questions?: MissingQuestion[];
  missing_summary?: string;
}

export interface QuoteItem {
  id: number;
  product_id: number | null;
  category_name: string | null;
  product_name: string;
  spec: string | null;
  unit: string;
  quantity: number;
  width: number | null;
  height: number | null;
  depth: number | null;
  unit_price: number;
  cost_price: number;
  material_cost: number;
  loss_cost: number;
  labor_cost: number;
  transport_cost: number;
  other_cost: number;
  total_cost: number;
  subtotal: number;
  profit_margin: number;
  final_price: number;
  formula: string | null;
  breakdown: Record<string, unknown>;
  match_confidence: number | null;
  remark: string | null;
}

export interface TierSummary {
  level: PlanLevel;
  name: string;
  total_amount: number;
  total_cost?: number;
  gross_margin?: number;
}

export interface Quote {
  id: number;
  quote_no: string;
  version_no: number;
  project_name: string;
  customer_name: string | null;
  customer_id: number | null;
  status: QuoteStatus;
  status_label: string;
  currency: string;
  subtotal: number;
  discount_amount: number;
  tax_rate: number;
  tax_amount: number;
  total_amount: number;
  total_cost: number;
  gross_profit: number;
  gross_margin: number;
  tiers: Record<string, TierSummary>;
  notes: string | null;
  payment_terms: string | null;
  service_terms: string | null;
  requirement_text: string | null;
  requirement_json: Record<string, unknown>;
  missing_fields: string[];
  confidence: number | null;
  valid_until: string | null;
  public_token: string | null;
  public_url: string | null;
  allow_download: boolean;
  view_count: number;
  first_viewed_at: string | null;
  last_viewed_at: string | null;
  created_at: string | null;
  sent_at: string | null;
  won_at: string | null;
  items: QuoteItem[];
}

export interface QuoteListItem {
  id: number;
  quote_no: string;
  project_name: string;
  customer_name: string | null;
  status: QuoteStatus;
  status_label: string;
  total_amount: number;
  total_cost: number;
  gross_margin: number;
  version_no: number;
  view_count: number;
  item_count: number;
  created_at: string | null;
  valid_until: string | null;
  last_viewed_at?: string | null;
  public_token: string | null;
}

export interface Customer {
  id: number;
  name: string;
  contact_name: string | null;
  phone: string | null;
  wechat: string | null;
  source: string | null;
  address: string | null;
  remark: string | null;
  status: CustomerStatus;
  tags: string[];
  quote_count: number;
  deal_count: number;
  total_amount: number;
  next_followup_at: string | null;
  last_contact_at: string | null;
  created_at: string | null;
}

export interface Product {
  id: number;
  name: string;
  category_id: number | null;
  category_name: string | null;
  model: string | null;
  spec: string | null;
  unit: string;
  pricing_mode: string;
  cost_price: number;
  default_price: number;
  min_price: number;
  loss_rate: number;
  labor_cost: number;
  labor_price_per_unit: number;
  transport_cost: number;
  other_cost: number;
  min_profit_margin: number;
  markup_rate: number;
  tax_rate: number;
  gross_margin_preview: number;
  is_active: boolean;
  remark: string | null;
}

export interface Category {
  id: number;
  name: string;
  code: string | null;
  description: string | null;
  sort_order: number;
  is_active: boolean;
  product_count: number;
}

export interface PriceRule {
  id: number;
  name: string;
  product_id: number | null;
  product_name: string | null;
  category_id: number | null;
  category_name: string | null;
  rule_type: string;
  priority: number;
  conditions: Record<string, unknown>;
  params: Record<string, unknown>;
  description: string | null;
  is_active: boolean;
}

export interface QuoteTemplate {
  id: number;
  name: string;
  accent_color: string;
  show_tiers: boolean;
  show_unit_price: boolean;
  payment_terms: string | null;
  service_terms: string | null;
  footer: string | null;
  is_default: boolean;
  layout: Record<string, unknown>;
}

export interface Followup {
  id: number;
  customer_id: number;
  customer_name: string | null;
  quote_id: number | null;
  user_id: number | null;
  status: string;
  content: string;
  next_followup_at: string | null;
  done: boolean;
  channel: string;
  created_at: string | null;
}

export interface DashboardData {
  greeting: string;
  stats: {
    today_quotes: number;
    pending_followups: number;
    month_quote_amount: number;
    month_deal_amount: number;
    total_quotes: number;
    total_deals: number;
    conversion_rate: number;
  };
  quote_trend: { date: string; amount: number; count: number }[];
  deal_trend: { date: string; amount: number }[];
  funnel: { stage: string; value: number }[];
  today_followups: {
    id: number;
    name: string;
    contact_name: string | null;
    phone: string | null;
    status: string;
    quote_count: number;
    total_amount: number;
    next_followup_at: string | null;
  }[];
  recent_quotes: QuoteListItem[];
  high_value_quotes: QuoteListItem[];
  followup_hint: string;
  ai_usage: AiUsage;
  company: { id: number; name: string; plan: string | null };
}

export interface AiUsage {
  month: string;
  calls: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
  quota: number;
  remaining: number;
  usage_ratio: number;
}

export interface Plan {
  id: number;
  code: string;
  name: string;
  tagline: string | null;
  price: number;
  billing_cycle: string;
  max_users: number;
  max_quotes: number;
  ai_quota: number;
  storage_quota_mb: number;
  features: string[];
  description: string | null;
  is_active?: boolean;
  company_count?: number;
}

export interface PublicQuotePayload {
  requires_password: boolean;
  quote: {
    quote_no: string;
    version_no: number;
    project_name: string;
    customer_name: string | null;
    status: string;
    subtotal: number;
    discount_amount: number;
    tax_amount: number;
    total_amount: number;
    tiers: Record<string, TierSummary>;
    items: {
      id: number;
      product_name: string;
      category_name: string | null;
      spec: string | null;
      unit: string;
      quantity: number;
      width: number | null;
      height: number | null;
      unit_price: number;
      final_price: number;
    }[];
    payment_terms: string | null;
    service_terms: string | null;
    notes: string | null;
    valid_until: string | null;
    created_at: string | null;
    allow_download: boolean;
    company: {
      name: string | null;
      contact_name: string | null;
      contact_phone: string | null;
      contact_wechat: string | null;
      address: string | null;
      logo_url: string | null;
    };
  } | null;
  company: Record<string, string | null> | null;
}

export interface AdminDashboard {
  stats: Record<string, number>;
  ai: {
    total_calls: number;
    today_calls: number;
    total_cost: number;
    today_cost: number;
    by_model: { model: string; calls: number; cost: number }[];
    by_company: { company_id: number; company_name: string; calls: number; cost: number }[];
    by_task: { task_type: string; calls: number }[];
  };
  trend: { date: string; companies: number; quotes: number; ai_calls: number }[];
  system: { env: string; ai_mode: string; redis: boolean; storage_backend: string; database: string };
}

export interface IndustryTemplateSummary {
  code: string;
  name: string;
  description: string;
  status: "available" | "coming_soon";
  sort_order: number;
  categories: string[];
  product_count: number;
  pricing_modes: { value: string; label: string }[];
  fields: {
    key: string;
    label: string;
    type: string;
    unit: string | null;
    required: boolean;
    options: string[];
    help_text: string;
  }[];
}
