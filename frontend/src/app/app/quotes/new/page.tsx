"use client";
import { AlertTriangle, ArrowLeft, ArrowRight, Check, FileSpreadsheet, FileText, Image as ImageIcon, Loader2, Plus, Sparkles, Trash2, Upload, Wand2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { InlineAlert } from "@/components/ui/states";
import { toast } from "@/components/ui/toast";
import { aiApi, errorMessage, quoteApi } from "@/lib/api";
import type { MissingQuestion, Requirement, RequirementItem } from "@/lib/types";
import { cn } from "@/lib/utils";
type Stage = "input" | "recognizing" | "review";
const RECOGNIZE_STEPS = ["读取图片", "分析文本", "识别产品", "提取参数", "检查缺失项"];
const UNITS = ["平方米", "米", "个", "套", "张", "块", "项", "公斤", "件", "车"];
const SAMPLE = "帮我做一个10米门头，铝塑板底，12个发光字，月底安装";
export default function NewQuotePage() {
  const router = useRouter();
  const [stage, setStage] = React.useState<Stage>("input");
  const [text, setText] = React.useState("");
  const [file, setFile] = React.useState<File | null>(null);
  const [dragging, setDragging] = React.useState(false);
  const [progress, setProgress] = React.useState(0);
  const [stepIndex, setStepIndex] = React.useState(0);
  const [requirement, setRequirement] = React.useState<Requirement | null>(null);
  const [questions, setQuestions] = React.useState<MissingQuestion[]>([]);
  const [aiMode, setAiMode] = React.useState("mock");
  const [customerName, setCustomerName] = React.useState("");
  const [creating, setCreating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);
  React.useEffect(() => {
    if (stage !== "recognizing") return;
    setStepIndex(0);
    const timer = window.setInterval(() => {
      setStepIndex((value) => (value < RECOGNIZE_STEPS.length - 1 ? value + 1 : value));
    }, 620);
    return () => window.clearInterval(timer);
  }, [stage]);
  React.useEffect(() => {
    if (!file) {
      setProgress(0);
      return;
    }
    setProgress(12);
    const timer = window.setInterval(() => {
      setProgress((value) => (value >= 96 ? 96 : value + Math.random() * 22));
    }, 180);
    return () => window.clearInterval(timer);
  }, [file]);
  function acceptFile(candidate: File | null | undefined) {
    if (!candidate) return;
    const allowed = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf", ".xlsx", ".xls", ".csv", ".txt"];
    const lower = candidate.name.toLowerCase();
    if (!allowed.some((extension) => lower.endsWith(extension))) {
      toast.error("仅支持 JPG / PNG / WEBP / PDF / XLSX / CSV 文件");
      return;
    }
    if (candidate.size > 20 * 1024 * 1024) {
      toast.error("文件大小不能超过 20MB");
      return;
    }
    setFile(candidate);
    setError(null);
  }
  async function recognize() {
    if (!file && !text.trim()) {
      setError("请上传截图/图片，或粘贴客户需求文字");
      return;
    }
    setError(null);
    setStage("recognizing");
    const started = Date.now();
    try {
      let result: Requirement;
      if (file) {
        const form = new FormData();
        form.append("file", file);
        if (text.trim()) form.append("text", text.trim());
        const response = await aiApi.extract(form);
        result = response.requirement;
      } else {
        const response = await aiApi.extractText(text.trim());
        result = response.requirement;
      }
      const elapsed = Date.now() - started;
      if (elapsed < 2400) await new Promise((resolve) => window.setTimeout(resolve, 2400 - elapsed));
      setRequirement(result);
      setQuestions(result.missing_questions ?? []);
      setAiMode(result.mode ?? "mock");
      setCustomerName(result.customer_name ?? "");
      setProgress(100);
      setStage("review");
    } catch (err) {
      setError(errorMessage(err));
      setStage("input");
    }
  }
  function updateItem(index: number, patch: Partial<RequirementItem>) {
    setRequirement((prev) => {
      if (!prev) return prev;
      const items = prev.items.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item));
      return { ...prev, items };
    });
  }
  function removeItem(index: number) {
    setRequirement((prev) => (prev ? { ...prev, items: prev.items.filter((_, itemIndex) => itemIndex !== index) } : prev));
  }
  function addItem() {
    setRequirement((prev) =>
      prev
        ? {
            ...prev,
            items: [
              ...prev.items,
              { product_name: "新增项目", category: null, unit: "个", quantity: 1, width: null, height: null },
            ],
          }
        : prev,
    );
  }
  async function createQuote() {
    if (!requirement || !requirement.items.length) {
      setError("请至少保留一个报价项目");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const quote = await quoteApi.create({
        project_name: requirement.project_name ?? "未命名项目",
        customer_name: customerName || requirement.customer_name || null,
        items: requirement.items,
        transport_required: requirement.transport_required ?? null,
        installation_required: requirement.installation_required ?? null,
        installation_location: requirement.installation_location ?? null,
        deadline: requirement.deadline ?? null,
        missing_fields: requirement.missing_fields ?? [],
        confidence: requirement.confidence ?? null,
        requirement_text: text || (file ? "上传文件：" + file.name : ""),
        industry_id: "advertising",
      });
      toast.success("报价已生成：" + quote.quote_no);
      router.push("/app/quotes/" + quote.id);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setCreating(false);
    }
  }
  const order: Stage[] = ["input", "recognizing", "review"];
  const activeIndex = order.indexOf(stage);
  return (
    <div>
      <PageHeader
        title="新建报价"
        description="上传客户需求，AI 识别 → 规则引擎计算 → 生成报价单"
        breadcrumb={
          <Link href="/app/quotes" className="inline-flex items-center gap-1 hover:text-ink">
            <ArrowLeft className="h-3.5 w-3.5" />
            返回报价列表
          </Link>
        }
        actions={
          stage === "review" ? (
            <Button
              variant="secondary"
              onClick={() => {
                setStage("input");
                setRequirement(null);
              }}
            >
              重新识别
            </Button>
          ) : null
        }
      />
      <div className="mb-6 flex flex-wrap items-center gap-2 text-[12.5px]">
        {["上传需求", "AI 识别", "确认并报价"].map((label, index) => {
          const done = index < activeIndex;
          const active = index === activeIndex;
          return (
            <div key={label} className="flex items-center gap-2">
              <span
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-full text-[11.5px] font-medium",
                  done ? "bg-success text-white" : active ? "bg-accent text-white" : "bg-line text-faint",
                )}
              >
                {done ? <Check className="h-3 w-3" /> : index + 1}
              </span>
              <span className={cn(active ? "font-medium text-ink" : "text-faint")}>{label}</span>
              {index < 2 ? <span className="mx-1 h-px w-8 bg-line" /> : null}
            </div>
          );
        })}
      </div>
      {error ? (
        <div className="mb-4">
          <InlineAlert tone="danger" title={error} />
        </div>
      ) : null}
      {stage === "input" ? (
        <div className="grid gap-4 lg:grid-cols-[1.35fr_1fr]">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>上传客户需求</CardTitle>
                <p className="mt-1 text-[12.5px] text-muted">
                  支持微信截图、图片、PDF、Excel，或直接粘贴一段文字
                </p>
              </div>
            </CardHeader>
            <CardContent>
              <div
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(event) => {
                  event.preventDefault();
                  setDragging(false);
                  acceptFile(event.dataTransfer.files?.[0]);
                }}
                onClick={() => inputRef.current?.click()}
                className={cn(
                  "flex cursor-pointer flex-col items-center justify-center rounded-[16px] border-2 border-dashed px-6 py-12 text-center transition-all",
                  dragging
                    ? "border-accent bg-accent-soft/60"
                    : "border-line-strong bg-surface-2 hover:border-accent/60 hover:bg-accent-soft/30",
                )}
              >
                <input
                  ref={inputRef}
                  type="file"
                  className="hidden"
                  accept=".jpg,.jpeg,.png,.webp,.gif,.pdf,.xlsx,.xls,.csv,.txt"
                  onChange={(event) => acceptFile(event.target.files?.[0])}
                />
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-surface text-accent shadow-[var(--shadow-subtle)]">
                  <Upload className="h-5 w-5" />
                </span>
                <p className="mt-4 text-[14px] font-medium text-ink">把微信截图拖到这里</p>
                <p className="mt-1 text-[12.5px] text-muted">或点击选择文件 · JPG / PNG / WEBP / PDF / XLSX / CSV · 最大 20MB</p>
                <div className="mt-5 flex flex-wrap items-center justify-center gap-2 text-[11.5px] text-faint">
                  <span className="flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1">
                    <ImageIcon className="h-3 w-3" />
                    微信截图
                  </span>
                  <span className="flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1">
                    <FileText className="h-3 w-3" />
                    PDF 需求
                  </span>
                  <span className="flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1">
                    <FileSpreadsheet className="h-3 w-3" />
                    Excel 清单
                  </span>
                </div>
              </div>
              {file ? (
                <div className="mt-4 rounded-[14px] border border-line bg-surface p-3.5">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-soft text-accent">
                      <FileText className="h-4 w-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[13.5px] font-medium text-ink">{file.name}</p>
                      <p className="text-[12px] text-faint">{(file.size / 1024).toFixed(0)} KB · 已就绪</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="iconSm"
                      onClick={(event) => {
                        event.stopPropagation();
                        setFile(null);
                      }}
                      aria-label="移除文件"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                  <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-line/70">
                    <div
                      className="h-full rounded-full bg-accent transition-[width] duration-300"
                      style={{ width: progress + "%" }}
                    />
                  </div>
                </div>
              ) : null}
              <div className="mt-5">
                <Field label="或者粘贴客户需求文字" hint="可以把微信聊天记录直接复制过来">
                  <Textarea
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                    placeholder="例如：帮我做一个10米门头，铝塑板底，12个发光字，月底安装"
                    className="min-h-[110px]"
                  />
                </Field>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setText(SAMPLE)}>
                    <Wand2 className="h-3.5 w-3.5" />
                    填入示例需求
                  </Button>
                  <span className="text-[12px] text-faint">或只上传截图，系统会自动识别</span>
                </div>
              </div>
              <div className="mt-5 flex flex-wrap gap-2">
                <Button size="lg" onClick={() => void recognize()}>
                  <Sparkles className="h-4 w-4" />
                  开始 AI 识别
                </Button>
                <Link href="/app/quotes/manual">
                  <Button variant="secondary" size="lg">
                    手动创建
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>识别前须知</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                {
                  title: "AI 只负责理解需求",
                  desc: "它不会给你定价，也不会自己编造产品与数字。识别不到的信息会标成缺失项。",
                },
                {
                  title: "识别结果可以随便改",
                  desc: "尺寸、数量、产品名、单位都能人工修正，改完由规则引擎重新计算。",
                },
                {
                  title: "价格来自你自己的价格库",
                  desc: "系统按产品匹配你的成本、损耗率、人工费与利润规则，计算过程完全可追溯。",
                },
              ].map((item) => (
                <div key={item.title} className="flex gap-3">
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-accent-soft">
                    <Check className="h-3 w-3 text-accent" />
                  </span>
                  <div>
                    <p className="text-[13.5px] font-medium text-ink">{item.title}</p>
                    <p className="mt-1 text-[12.5px] leading-relaxed text-muted">{item.desc}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      ) : null}
      {stage === "recognizing" ? (
        <Card>
          <CardContent className="py-10">
            <div className="mx-auto max-w-md text-center">
              <div className="relative mx-auto flex h-16 w-16 items-center justify-center">
                <span className="absolute inset-0 animate-ping rounded-full bg-accent/15" />
                <span className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-accent text-white shadow-[var(--shadow-accent)]">
                  <Sparkles className="h-6 w-6" />
                </span>
              </div>
              <h2 className="mt-6 text-[19px] font-semibold tracking-tight text-ink">AI 正在理解客户需求</h2>
              <p className="mt-2 text-[13.5px] text-muted">正在读取图片、分析文本、匹配你的产品价格库…</p>
              <div className="mt-8 space-y-2.5 text-left">
                {RECOGNIZE_STEPS.map((label, index) => {
                  const done = index < stepIndex;
                  const active = index === stepIndex;
                  return (
                    <div
                      key={label}
                      className={cn(
                        "flex items-center gap-3 rounded-xl border px-4 py-3 transition-all",
                        active ? "border-accent/40 bg-accent-soft/60" : "border-line bg-surface",
                      )}
                    >
                      <span
                        className={cn(
                          "flex h-5 w-5 items-center justify-center rounded-full",
                          done ? "bg-success-soft text-success" : active ? "bg-accent text-white" : "bg-line text-faint",
                        )}
                      >
                        {done ? (
                          <Check className="h-3 w-3" />
                        ) : active ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <span className="h-1.5 w-1.5 rounded-full bg-current" />
                        )}
                      </span>
                      <span className={cn("text-[13px]", active ? "font-medium text-ink" : "text-muted")}>{label}</span>
                      {done ? <span className="ml-auto text-[11.5px] text-faint">完成</span> : null}
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}
      {stage === "review" && requirement ? (
        <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
          <div className="space-y-4">
            {requirement.missing_fields.length ? (
              <InlineAlert
                tone="warning"
                title={"还有 " + requirement.missing_fields.length + " 项信息可能影响最终报价"}
                action={<Badge tone="warning">建议先向客户确认</Badge>}
              >
                {requirement.missing_fields.join(" · ")}
              </InlineAlert>
            ) : (
              <InlineAlert tone="success" title="需求信息完整，可以直接开始报价" />
            )}
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>识别结果（所有字段都可以修改）</CardTitle>
                  <p className="mt-1 text-[12.5px] text-muted">
                    模式：{aiMode === "mock" ? "Mock 演示模式" : "DeepSeek 真实识别"} · 置信度{" "}
                    {(requirement.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                <Button variant="ghost" size="sm" onClick={addItem}>
                  <Plus className="h-3.5 w-3.5" />
                  添加项目
                </Button>
              </CardHeader>
              <CardContent className="space-y-3">
                {requirement.items.map((item, index) => (
                  <div key={index} className="rounded-[14px] border border-line bg-surface-2/60 p-4">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Badge tone="neutral">{item.category ?? "未分类"}</Badge>
                        <span className="text-[12.5px] text-faint">第 {index + 1} 项</span>
                      </div>
                      <Button variant="ghost" size="iconSm" onClick={() => removeItem(index)} aria-label="删除">
                        <Trash2 className="h-3.5 w-3.5 text-danger" />
                      </Button>
                    </div>
                    <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                      <Field label="产品名称" className="sm:col-span-2">
                        <Input
                          value={item.product_name}
                          onChange={(event) => updateItem(index, { product_name: event.target.value })}
                        />
                      </Field>
                      <Field label="数量">
                        <Input
                          type="number"
                          step="0.01"
                          value={item.quantity ?? 1}
                          onChange={(event) => updateItem(index, { quantity: Number(event.target.value) })}
                        />
                      </Field>
                      <Field label="单位">
                        <Select value={item.unit} onChange={(event) => updateItem(index, { unit: event.target.value })}>
                          {UNITS.map((unit) => (
                            <option key={unit} value={unit}>
                              {unit}
                            </option>
                          ))}
                        </Select>
                      </Field>
                      <Field label="宽度（米）" hint={item.width ? undefined : "缺失"}>
                        <Input
                          type="number"
                          step="0.01"
                          value={item.width ?? ""}
                          placeholder="例如 10"
                          onChange={(event) =>
                            updateItem(index, { width: event.target.value === "" ? null : Number(event.target.value) })
                          }
                        />
                      </Field>
                      <Field label="高度（米）" hint={item.height ? undefined : "缺失"}>
                        <Input
                          type="number"
                          step="0.01"
                          value={item.height ?? ""}
                          placeholder="例如 1.5"
                          onChange={(event) =>
                            updateItem(index, { height: event.target.value === "" ? null : Number(event.target.value) })
                          }
                        />
                      </Field>
                      <Field label="厚度（米）">
                        <Input
                          type="number"
                          step="0.01"
                          value={item.depth ?? ""}
                          onChange={(event) =>
                            updateItem(index, { depth: event.target.value === "" ? null : Number(event.target.value) })
                          }
                        />
                      </Field>
                      <Field label="材质">
                        <Input
                          value={item.material ?? ""}
                          placeholder="例如 不锈钢"
                          onChange={(event) => updateItem(index, { material: event.target.value })}
                        />
                      </Field>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>项目信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Field label="项目名称">
                  <Input
                    value={requirement.project_name ?? ""}
                    onChange={(event) => setRequirement({ ...requirement, project_name: event.target.value })}
                  />
                </Field>
                <Field label="客户名称" hint="填写后会自动创建客户档案">
                  <Input
                    value={customerName}
                    placeholder="例如：XX餐饮（万达店）"
                    onChange={(event) => setCustomerName(event.target.value)}
                  />
                </Field>
                <Field label="安装地址">
                  <Input
                    value={requirement.installation_location ?? ""}
                    placeholder="影响运输与高空作业费用"
                    onChange={(event) => setRequirement({ ...requirement, installation_location: event.target.value })}
                  />
                </Field>
                <Field label="交付时间">
                  <Input
                    value={requirement.deadline ?? ""}
                    placeholder="例如 月底"
                    onChange={(event) => setRequirement({ ...requirement, deadline: event.target.value })}
                  />
                </Field>
              </CardContent>
            </Card>
            {questions.length ? (
              <Card>
                <CardHeader>
                  <CardTitle>建议向客户确认</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {questions.map((question) => (
                    <div key={question.field} className="rounded-xl border border-line bg-surface-2 p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[12.5px] font-medium text-ink-soft">{question.field}</span>
                        <Badge tone={question.impact === "high" ? "warning" : "neutral"}>
                          {question.impact === "high" ? "影响较大" : "一般"}
                        </Badge>
                      </div>
                      <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted">{question.question}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            ) : null}
            {requirement.unknown_fields?.length ? (
              <InlineAlert tone="info" title="未能识别的信息">
                {requirement.unknown_fields.join(" · ")}
              </InlineAlert>
            ) : null}
            <Card>
              <CardContent className="pt-5">
                <div className="flex items-start gap-2.5 rounded-xl bg-surface-2 p-3.5 text-[12.5px] text-muted">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                  <span>
                    点击下方按钮后，系统会用你企业自己的价格库和规则引擎计算价格，AI 不参与定价。计算完成后可以继续修改并重新计算。
                  </span>
                </div>
                <Button className="mt-4 w-full" size="lg" loading={creating} onClick={() => void createQuote()}>
                  <Sparkles className="h-4 w-4" />
                  确认并开始报价
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      ) : null}
    </div>
  );
}

