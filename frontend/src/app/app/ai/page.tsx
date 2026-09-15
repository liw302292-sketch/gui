"use client";
import { Activity, AlertTriangle, Copy, Gauge, Layers, MessageSquare, Sparkles, TrendingUp, Upload } from "lucide-react";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { EmptyState, InlineAlert, PageLoading } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { Tabs } from "@/components/ui/tabs";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { aiApi, errorMessage } from "@/lib/api";
import type { Requirement } from "@/lib/types";
import { formatCurrency, formatDate, formatPercent } from "@/lib/utils";
const TABS = [
  { value: "extract", label: "需求识别" },
  { value: "reply", label: "客户回复" },
  { value: "explain", label: "报价解释" },
  { value: "suggest", label: "报价参考" },
  { value: "usage", label: "用量统计" },
];
export default function AiAssistantPage() {
  const status = useApiData(() => aiApi.status(), []);
  const usage = useApiData(() => aiApi.usage(), []);
  const [tab, setTab] = React.useState("extract");
  const [busy, setBusy] = React.useState(false);
  const [text, setText] = React.useState("");
  const [requirement, setRequirement] = React.useState<Requirement | null>(null);
  const [questions, setQuestions] = React.useState<{ field: string; question: string; impact: string }[]>([]);
  const [replyStyle, setReplyStyle] = React.useState("professional");
  const [replyText, setReplyText] = React.useState("");
  const [explainQuestion, setExplainQuestion] = React.useState("为什么这么贵？");
  const [explain, setExplain] = React.useState<{ reasons: string[]; customer_reply: string; adjust_options: string[] } | null>(null);
  const [suggestion, setSuggestion] = React.useState<{
    range_low: number | null;
    range_high: number | null;
    basis: string;
    sample_size: number;
    confidence: number;
    caution: string;
  } | null>(null);
  const fileRef = React.useRef<HTMLInputElement>(null);
  async function extractText() {
    if (!text.trim()) {
      toast.error("请先粘贴客户需求文字");
      return;
    }
    setBusy(true);
    try {
      const result = await aiApi.extractText(text.trim());
      setRequirement(result.requirement);
      setQuestions(result.requirement.missing_questions ?? []);
      toast.success("识别完成");
      usage.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }
  async function extractFile(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    try {
      const form = new FormData();
      form.append("file", file);
      if (text.trim()) form.append("text", text.trim());
      const result = await aiApi.extract(form);
      setRequirement(result.requirement);
      setQuestions(result.requirement.missing_questions ?? []);
      toast.success("识别完成");
      usage.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }
  async function makeReply() {
    setBusy(true);
    try {
      const result = await aiApi.reply(
        (requirement as unknown as Record<string, unknown>) ?? { items: [] },
        { total_amount: 0 },
        replyStyle,
      );
      setReplyText(result.result.content);
      usage.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }
  async function makeExplain() {
    setBusy(true);
    try {
      const result = await aiApi.explain({ total_amount: 0, items: [] }, explainQuestion);
      setExplain(result.result);
      usage.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }
  async function makeSuggestion() {
    setBusy(true);
    try {
      const result = await aiApi.suggestPrice(
        (requirement as unknown as Record<string, unknown>) ?? { items: [] },
        requirement?.items?.[0]?.category ?? null,
      );
      setSuggestion(result.result);
      usage.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }
  async function copy(value: string, label: string) {
    try {
      await navigator.clipboard.writeText(value);
      toast.success(label + "已复制");
    } catch {
      toast.error("复制失败");
    }
  }
  const summary = usage.data?.summary ?? status.data?.usage;
  const quotaRatio = summary?.quota ? Math.min(summary.calls / summary.quota, 1) : 0;
  return (
    <div>
      <PageHeader
        title="AI 助手"
        description="识别需求、生成回复、解释报价、参考区间。AI 不参与定价。"
        actions={
          <Badge tone={status.data?.mode === "real" ? "success" : "accent"}>
            {status.data?.mode === "real" ? "DeepSeek 真实模式" : "Mock 演示模式"}
          </Badge>
        }
      />
      {status.data?.mode === "mock" ? (
        <InlineAlert tone="info" title="当前使用 Mock 模式：未配置 DEEPSEEK_API_KEY">
          系统会用确定性演示数据跑通完整流程。在 .env 中填写 DEEPSEEK_API_KEY 并设置 AI_MODE=real 后自动切换真实 AI，不需要改代码。
        </InlineAlert>
      ) : null}
      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="本月 AI 调用" value={String(summary?.calls ?? 0)} unit="次" icon={<Activity className="h-4 w-4" />} />
        <StatCard label="本月额度" value={String(summary?.quota ?? 0)} unit="次" tone="accent" icon={<Gauge className="h-4 w-4" />} />
        <StatCard label="Token 消耗" value={String((summary?.input_tokens ?? 0) + (summary?.output_tokens ?? 0))} unit="tokens" />
        <StatCard label="预估成本" value={formatCurrency(summary?.estimated_cost ?? 0)} />
      </div>
      <Card className="mt-4">
        <CardContent className="pt-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Tabs tabs={TABS} value={tab} onChange={setTab} />
            <span className="text-[12px] text-faint">
              模型：{status.data?.models.vision ?? "-"}（图片）/ {status.data?.models.reasoning ?? "-"}（复杂分析）
            </span>
          </div>
          <div className="mt-4">
            <Progress value={quotaRatio} tone={quotaRatio > 0.9 ? "danger" : quotaRatio > 0.7 ? "warning" : "accent"} />
            <p className="mt-2 text-[12px] text-faint">
              额度使用 {summary?.calls ?? 0} / {summary?.quota ?? 0}（{formatPercent(quotaRatio)}），超过额度后需要升级套餐
            </p>
          </div>
        </CardContent>
      </Card>
      <div className="mt-4">
        {tab === "extract" ? (
          <div className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>上传需求</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <input
                  ref={fileRef}
                  type="file"
                  accept=".jpg,.jpeg,.png,.webp,.gif,.pdf,.xlsx,.xls,.csv,.txt"
                  className="hidden"
                  onChange={(event) => void extractFile(event.target.files?.[0])}
                />
                <button
                  type="button"
                  onClick={() => fileRef.current?.click()}
                  className="flex w-full flex-col items-center justify-center rounded-[16px] border-2 border-dashed border-line-strong bg-surface-2 px-5 py-9 text-center transition-colors hover:border-accent/60 hover:bg-accent-soft/30"
                >
                  <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-surface text-accent shadow-[var(--shadow-subtle)]">
                    <Upload className="h-4.5 w-4.5" />
                  </span>
                  <p className="mt-3 text-[13.5px] font-medium text-ink">上传微信截图 / 图片 / PDF / Excel</p>
                  <p className="mt-1 text-[12px] text-faint">最大 20MB</p>
                </button>
                <Field label="或者粘贴需求文字">
                  <Textarea
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                    placeholder="帮我做一个10米门头，铝塑板底，12个发光字，月底安装"
                  />
                </Field>
                <Button loading={busy} onClick={() => void extractText()}>
                  <Sparkles className="h-4 w-4" />
                  开始识别
                </Button>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>识别结果</CardTitle>
                {requirement ? <Badge tone="accent">置信度 {formatPercent(requirement.confidence, 0)}</Badge> : null}
              </CardHeader>
              <CardContent>
                {requirement ? (
                  <div className="space-y-4">
                    <div className="rounded-xl border border-line bg-surface-2 p-3.5">
                      <p className="text-[13px] font-medium text-ink">{requirement.project_name ?? "未命名项目"}</p>
                      <p className="mt-1 text-[12px] text-faint">
                        识别到 {requirement.items.length} 个报价项
                        {requirement.deadline ? " · 交期 " + requirement.deadline : ""}
                      </p>
                    </div>
                    <div className="space-y-2.5">
                      {requirement.items.map((item, index) => (
                        <div key={index} className="rounded-xl border border-line p-3">
                          <div className="flex items-center justify-between">
                            <span className="text-[13px] font-medium text-ink">{item.product_name}</span>
                            <Badge tone="neutral">{item.category ?? "未分类"}</Badge>
                          </div>
                          <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-[12px] text-muted">
                            <span>数量：{item.quantity} {item.unit}</span>
                            <span>
                              尺寸：
                              {item.width && item.height ? item.width + "m × " + item.height + "m" : "待确认"}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                    {requirement.missing_fields.length ? (
                      <InlineAlert tone="warning" title={"还有 " + requirement.missing_fields.length + " 项信息待确认"}>
                        {requirement.missing_fields.join(" · ")}
                      </InlineAlert>
                    ) : null}
                    {questions.length ? (
                      <div className="space-y-2">
                        {questions.map((question) => (
                          <div key={question.field} className="rounded-xl border border-line bg-surface-2 p-3">
                            <p className="text-[12.5px] font-medium text-ink-soft">{question.field}</p>
                            <p className="mt-1 text-[12px] text-muted">{question.question}</p>
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <EmptyState
                    icon={<Sparkles className="h-5 w-5" />}
                    title="还没有识别结果"
                    description="上传截图或粘贴文字后，识别结果会显示在这里。"
                    className="py-10"
                  />
                )}
              </CardContent>
            </Card>
          </div>
        ) : null}
        {tab === "reply" ? (
          <Card>
            <CardHeader>
              <CardTitle>生成客户回复</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="回复风格">
                  <Select value={replyStyle} onChange={(event) => setReplyStyle(event.target.value)}>
                    <option value="professional">专业版</option>
                    <option value="concise">简洁版</option>
                    <option value="closing">成交版</option>
                  </Select>
                </Field>
                <Field label="识别到的项目">
                  <Input value={requirement ? requirement.items.length + " 个项目" : "请先在上方完成需求识别"} readOnly />
                </Field>
              </div>
              <Button loading={busy} onClick={() => void makeReply()}>
                <MessageSquare className="h-4 w-4" />
                生成回复文案
              </Button>
              {replyText ? (
                <div className="rounded-xl border border-line bg-surface-2 p-4">
                  <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-ink-soft">{replyText}</p>
                  <Button variant="secondary" size="sm" className="mt-3" onClick={() => void copy(replyText, "文案")}>
                    <Copy className="h-3.5 w-3.5" />
                    复制
                  </Button>
                </div>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
        {tab === "explain" ? (
          <Card>
            <CardHeader>
              <CardTitle>客户嫌贵，怎么解释</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Field label="客户的疑问">
                <Input value={explainQuestion} onChange={(event) => setExplainQuestion(event.target.value)} />
              </Field>
              <Button loading={busy} onClick={() => void makeExplain()}>
                <AlertTriangle className="h-4 w-4" />
                生成解释
              </Button>
              {explain ? (
                <div className="space-y-3">
                  <div className="rounded-xl border border-line bg-surface-2 p-4">
                    <p className="text-[12.5px] font-medium text-ink">可直接发给客户</p>
                    <p className="mt-2 whitespace-pre-wrap text-[13px] leading-relaxed text-ink-soft">
                      {explain.customer_reply}
                    </p>
                    <Button variant="secondary" size="sm" className="mt-3" onClick={() => void copy(explain.customer_reply, "解释")}>
                      <Copy className="h-3.5 w-3.5" />
                      复制
                    </Button>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-xl border border-line p-4">
                      <p className="text-[12.5px] font-medium text-ink">价格构成要点</p>
                      <ul className="mt-2 space-y-1.5">
                        {explain.reasons.map((reason) => (
                          <li key={reason} className="text-[12px] leading-relaxed text-muted">
                            · {reason}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="rounded-xl border border-line p-4">
                      <p className="text-[12.5px] font-medium text-ink">可选降本方向</p>
                      <ul className="mt-2 space-y-1.5">
                        {explain.adjust_options.map((option) => (
                          <li key={option} className="text-[12px] leading-relaxed text-muted">
                            · {option}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
        {tab === "suggest" ? (
          <Card>
            <CardHeader>
              <CardTitle>历史报价参考区间</CardTitle>
              <Badge tone="warning">只给区间，不决定最终价格</Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-xl border border-line bg-surface-2 p-4 text-[12.5px] text-muted">
                AI 会读取你企业历史「已成交」报价，给出参考区间。最终价格仍然必须由规则引擎计算。
              </div>
              <Button loading={busy} onClick={() => void makeSuggestion()}>
                <TrendingUp className="h-4 w-4" />
                生成参考区间
              </Button>
              {suggestion ? (
                <div className="space-y-3">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[14px] border border-accent/30 bg-accent-soft/40 p-4">
                      <p className="text-[12.5px] text-muted">建议区间</p>
                      <p className="mt-2 text-[20px] font-semibold text-ink">
                        {suggestion.range_low && suggestion.range_high
                          ? formatCurrency(suggestion.range_low) + " ~ " + formatCurrency(suggestion.range_high)
                          : "样本不足"}
                      </p>
                    </div>
                    <div className="rounded-[14px] border border-line p-4">
                      <p className="text-[12.5px] text-muted">样本量 / 置信度</p>
                      <p className="mt-2 text-[20px] font-semibold text-ink">
                        {suggestion.sample_size} 条 · {formatPercent(suggestion.confidence, 0)}
                      </p>
                    </div>
                  </div>
                  <div className="rounded-xl border border-line p-4">
                    <p className="text-[12.5px] font-medium text-ink">依据</p>
                    <p className="mt-1.5 text-[12.5px] text-muted">{suggestion.basis}</p>
                    <p className="mt-2 text-[12px] text-warning">{suggestion.caution}</p>
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
        {tab === "usage" ? (
          <Card>
            <CardHeader>
              <CardTitle>AI 调用记录</CardTitle>
              <Badge tone="neutral">{(usage.data?.recent_tasks ?? []).length} 条</Badge>
            </CardHeader>
            <CardContent className="px-0 pb-0">
              {usage.loading ? (
                <PageLoading />
              ) : !usage.data?.recent_tasks.length ? (
                <EmptyState icon={<Layers className="h-5 w-5" />} title="暂无调用记录" className="m-5" />
              ) : (
                <Table>
                  <THead>
                    <Th>任务</Th>
                    <Th>模型</Th>
                    <Th className="text-right">Token</Th>
                    <Th className="text-right">成本</Th>
                    <Th className="text-right">耗时</Th>
                    <Th>状态</Th>
                    <Th>时间</Th>
                  </THead>
                  <TBody>
                    {usage.data.recent_tasks.map((task) => (
                      <Tr key={task.id}>
                        <Td className="font-medium text-ink">{taskTypeLabel(task.task_type)}</Td>
                        <Td className="font-mono text-[11.5px] text-muted">{task.model}</Td>
                        <Td className="text-right tabular-nums text-muted">
                          {task.input_tokens} / {task.output_tokens}
                        </Td>
                        <Td className="text-right tabular-nums text-muted">{formatCurrency(task.estimated_cost)}</Td>
                        <Td className="text-right tabular-nums text-muted">{task.latency_ms} ms</Td>
                        <Td>
                          <Badge tone={task.status === "success" ? "success" : task.status === "failed" ? "danger" : "warning"}>
                            {task.status === "success" ? "成功" : task.status === "failed" ? "失败" : "处理中"}
                          </Badge>
                        </Td>
                        <Td className="text-[12px] text-faint">{formatDate(task.created_at, true)}</Td>
                      </Tr>
                    ))}
                  </TBody>
                </Table>
              )}
            </CardContent>
          </Card>
        ) : null}
      </div>
      <p className="mt-4 text-[12px] text-faint">
        模型配置来自环境变量（DEEPSEEK_TEXT_MODEL / REASONING_MODEL / VISION_MODEL），换模型不需要修改业务代码。
      </p>
    </div>
  );
}
function taskTypeLabel(type: string) {
  const map: Record<string, string> = {
    requirement_extract: "需求识别",
    missing_fields: "缺失信息补问",
    reply_draft: "客户回复文案",
    price_explain: "报价解释",
    price_suggestion: "报价区间建议",
  };
  return map[type] ?? type;
}

