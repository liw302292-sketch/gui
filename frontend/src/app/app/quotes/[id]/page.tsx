"use client";
import { ArrowLeft, Calculator, Check, Copy, Download, ExternalLink, History, Link2, MessageSquare, Send, Sparkles, Trash2, TrendingUp } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfirmDialog, Dialog } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { EmptyState, ErrorState, PageLoading } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { aiApi, errorMessage, quoteApi } from "@/lib/api";
import type { Quote } from "@/lib/types";
import { cn, formatCurrency, formatDate, formatPercent, relativeTime } from "@/lib/utils";
const STATUS_OPTIONS = [
  { value: "draft", label: "草稿" },
  { value: "sent", label: "已发送" },
  { value: "viewed", label: "已查看" },
  { value: "following", label: "待跟进" },
  { value: "won", label: "已成交" },
  { value: "void", label: "已作废" },
];
export default function QuoteDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const quoteId = Number(params.id);
  const { data: quote, loading, error, reload } = useApiData(() => quoteApi.detail(quoteId), [quoteId]);
  const [expanded, setExpanded] = React.useState<number | null>(null);
  const [sendOpen, setSendOpen] = React.useState(false);
  const [validDays, setValidDays] = React.useState(15);
  const [password, setPassword] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const [publicUrl, setPublicUrl] = React.useState<string | null>(null);
  const [voidOpen, setVoidOpen] = React.useState(false);
  const [replyOpen, setReplyOpen] = React.useState(false);
  const [replyStyle, setReplyStyle] = React.useState("professional");
  const [replyText, setReplyText] = React.useState("");
  const [aiLoading, setAiLoading] = React.useState(false);
  const [explainOpen, setExplainOpen] = React.useState(false);
  const [question, setQuestion] = React.useState("为什么这么贵？");
  const [explain, setExplain] = React.useState<{ reasons: string[]; customer_reply: string; adjust_options: string[] } | null>(null);
  const versions = useApiData(() => quoteApi.versions(quoteId), [quoteId]);
  const audit = useApiData(() => quoteApi.audit(quoteId), [quoteId]);
  if (loading) return <PageLoading label="正在加载报价…" />;
  if (error || !quote) return <ErrorState message={error ?? "报价不存在"} onRetry={reload} />;
  const tiers = Object.values(quote.tiers ?? {});
  const currentQuote = quote;
  const send = async () => {
    setSending(true);
    try {
      const result = await quoteApi.send(quoteId, { valid_days: validDays, password: password || null });
      setPublicUrl(result.public_url);
      toast.success("公开报价链接已生成");
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSending(false);
    }
  };
  const changeStatus = async (status: string) => {
    try {
      await quoteApi.setStatus(quoteId, status);
      toast.success("状态已更新");
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    }
  };
  const generateReply = async () => {
    setAiLoading(true);
    try {
      const result = await aiApi.reply(currentQuote.requirement_json ?? {}, quoteToAiPayload(currentQuote), replyStyle);
      setReplyText(result.result.content);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setAiLoading(false);
    }
  };
  const generateExplain = async () => {
    setAiLoading(true);
    try {
      const result = await aiApi.explain(quoteToAiPayload(currentQuote), question);
      setExplain(result.result);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setAiLoading(false);
    }
  };
  const copy = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(label + "已复制");
    } catch {
      toast.error("复制失败，请手动选择复制");
    }
  };
  return (
    <div>
      <PageHeader
        title={quote.project_name}
        description={
          <span className="flex flex-wrap items-center gap-2">
            <span className="font-mono">{quote.quote_no}</span>
            <span className="text-faint">V{quote.version_no}</span>
            <StatusBadge status={quote.status} label={quote.status_label} />
            {quote.view_count > 0 ? (
              <Badge tone="accent">客户已查看 {quote.view_count} 次</Badge>
            ) : null}
          </span>
        }
        breadcrumb={
          <Link href="/app/quotes" className="inline-flex items-center gap-1 hover:text-ink">
            <ArrowLeft className="h-3.5 w-3.5" />
            返回报价列表
          </Link>
        }
        actions={
          <>
            <Select value={quote.status} onChange={(event) => void changeStatus(event.target.value)} className="h-9 w-28 text-[13px]">
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
            <a href={quoteApi.pdfUrl(quoteId)} target="_blank" rel="noreferrer">
              <Button variant="secondary">
                <Download className="h-4 w-4" />
                下载 PDF
              </Button>
            </a>
            <Button onClick={() => setSendOpen(true)}>
              <Send className="h-4 w-4" />
              发送给客户
            </Button>
          </>
        }
      />
      <div className="grid gap-4 xl:grid-cols-[1.55fr_1fr]">
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-[16px] border border-line bg-surface p-4">
              <p className="text-[12.5px] text-muted">报价总额</p>
              <p className="mt-2 text-[26px] font-semibold leading-none tabular-nums text-ink">{formatCurrency(quote.total_amount)}</p>
              <p className="mt-2 text-[12px] text-faint">有效期至 {formatDate(quote.valid_until)}</p>
            </div>
            <div className="rounded-[16px] border border-line bg-surface p-4">
              <p className="text-[12.5px] text-muted">总成本（内部）</p>
              <p className="mt-2 text-[26px] font-semibold leading-none tabular-nums text-ink">{formatCurrency(quote.total_cost)}</p>
              <p className="mt-2 text-[12px] text-faint">含材料、损耗、人工、运输</p>
            </div>
            <div className="rounded-[16px] border border-success/20 bg-success-soft/40 p-4">
              <p className="text-[12.5px] text-muted">毛利 / 毛利率</p>
              <p className="mt-2 text-[26px] font-semibold leading-none tabular-nums text-ink">{formatCurrency(quote.gross_profit)}</p>
              <p className="mt-2 text-[12px] text-success">毛利率 {formatPercent(quote.gross_margin)}</p>
            </div>
          </div>
          {quote.tiers && tiers.length ? (
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>三档方案</CardTitle>
                  <p className="mt-1 text-[12.5px] text-muted">客户看到的是方案，成本与利润率只有你能看到</p>
                </div>
                <Badge tone="accent">当前标准版 {formatCurrency(quote.total_amount)}</Badge>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 sm:grid-cols-3">
                  {["economy", "standard", "premium"].map((level) => {
                    const tier = quote.tiers[level];
                    if (!tier) return null;
                    const active = level === "standard";
                    return (
                      <div
                        key={level}
                        className={cn(
                          "rounded-[14px] border p-4",
                          active ? "border-accent bg-accent-soft/40" : "border-line bg-surface-2/60",
                        )}
                      >
                        <p className="text-[12.5px] text-muted">{tier.name}</p>
                        <p className="mt-2 text-[20px] font-semibold tabular-nums text-ink">{formatCurrency(tier.total_amount)}</p>
                        {tier.gross_margin !== undefined ? (
                          <p className="mt-1.5 text-[11.5px] text-faint">毛利率 {formatPercent(tier.gross_margin)}</p>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ) : null}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>报价明细</CardTitle>
                <p className="mt-1 text-[12.5px] text-muted">点击任意一行查看完整计算过程</p>
              </div>
              <Badge tone="neutral">{quote.items.length} 项</Badge>
            </CardHeader>
            <CardContent className="px-0 pb-0">
              <Table>
                <THead>
                  <Th>产品 / 规格</Th>
                  <Th className="text-right">数量</Th>
                  <Th className="text-right">单价</Th>
                  <Th className="text-right">成本</Th>
                  <Th className="text-right">毛利率</Th>
                  <Th className="text-right">小计</Th>
                </THead>
                <TBody>
                  {quote.items.map((item) => (
                    <React.Fragment key={item.id}>
                      <Tr
                        className="cursor-pointer"
                        onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                      >
                        <Td>
                          <p className="font-medium text-ink">{item.product_name}</p>
                          <p className="mt-0.5 text-[12px] text-faint">
                            {[item.category_name, item.spec, item.width && item.height ? item.width + "m × " + item.height + "m" : null]
                              .filter(Boolean)
                              .join(" · ")}
                          </p>
                        </Td>
                        <Td className="text-right tabular-nums">
                          {item.quantity} {item.unit}
                        </Td>
                        <Td className="text-right tabular-nums">{formatCurrency(item.unit_price)}</Td>
                        <Td className="text-right tabular-nums text-muted">{formatCurrency(item.total_cost)}</Td>
                        <Td className="text-right tabular-nums text-success">{formatPercent(item.profit_margin)}</Td>
                        <Td className="text-right font-medium tabular-nums text-ink">{formatCurrency(item.final_price)}</Td>
                      </Tr>
                      {expanded === item.id ? (
                        <tr className="bg-surface-2">
                          <td colSpan={6} className="px-4 py-4">
                            <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
                              <div>
                                <p className="text-[12.5px] font-medium text-ink">计算过程（为什么是这个价格）</p>
                                <p className="mt-2 whitespace-pre-wrap rounded-xl border border-line bg-surface p-3 text-[12px] leading-relaxed text-ink-soft">
                                  {item.formula ?? "—"}
                                </p>
                              </div>
                              <div>
                                <p className="text-[12.5px] font-medium text-ink">成本构成</p>
                                <div className="mt-2 space-y-1 rounded-xl border border-line bg-surface p-3 text-[12.5px]">
                                  {[
                                    ["材料成本", item.material_cost],
                                    ["损耗", item.loss_cost],
                                    ["人工费", item.labor_cost],
                                    ["运输费", item.transport_cost],
                                    ["其他费用", item.other_cost],
                                  ].map(([label, value]) => (
                                    <div key={String(label)} className="flex items-center justify-between">
                                      <span className="text-muted">{label}</span>
                                      <span className="tabular-nums text-ink-soft">{formatCurrency(Number(value))}</span>
                                    </div>
                                  ))}
                                  <div className="flex items-center justify-between border-t border-line pt-1.5">
                                    <span className="font-medium text-ink">成本合计</span>
                                    <span className="font-medium tabular-nums text-ink">{formatCurrency(item.total_cost)}</span>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <span className="font-medium text-ink">对客售价</span>
                                    <span className="font-medium tabular-nums text-ink">{formatCurrency(item.final_price)}</span>
                                  </div>
                                </div>
                                {item.match_confidence !== null ? (
                                  <p className="mt-2 text-[11.5px] text-faint">
                                    价格库匹配置信度 {(item.match_confidence * 100).toFixed(0)}%
                                  </p>
                                ) : null}
                              </div>
                            </div>
                          </td>
                        </tr>
                      ) : null}
                    </React.Fragment>
                  ))}
                </TBody>
              </Table>
              <div className="border-t border-line px-5 py-4">
                <div className="ml-auto max-w-sm space-y-2 text-[13px]">
                  <Row label="小计" value={formatCurrency(quote.subtotal)} />
                  {quote.discount_amount ? <Row label="优惠" value={"-" + formatCurrency(quote.discount_amount)} /> : null}
                  {quote.tax_amount ? <Row label="税费" value={formatCurrency(quote.tax_amount)} /> : null}
                  <div className="flex items-center justify-between border-t border-ink pt-2.5">
                    <span className="font-medium text-ink">合计</span>
                    <span className="text-[20px] font-semibold tabular-nums text-ink">{formatCurrency(quote.total_amount)}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>AI 商务助手</CardTitle>
              <Badge tone="neutral">只生成文案，不改价格</Badge>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              <Button variant="secondary" onClick={() => { setReplyOpen(true); setReplyText(""); }}>
                <MessageSquare className="h-4 w-4" />
                生成客户回复
              </Button>
              <Button variant="secondary" onClick={() => { setExplainOpen(true); setExplain(null); }}>
                <Sparkles className="h-4 w-4" />
                客户嫌贵怎么解释
              </Button>
              <Link href={"/app/ai?quote=" + quoteId}>
                <Button variant="ghost">
                  <Calculator className="h-4 w-4" />
                  查看建议报价区间
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>客户信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2.5 text-[13px]">
              <Row label="客户名称" value={quote.customer_name ?? "未指定"} />
              {quote.customer_id ? (
                <Link href={"/app/customers/" + quote.customer_id} className="block text-[12.5px] text-accent hover:underline">
                  查看客户档案 →
                </Link>
              ) : null}
              <Row label="创建时间" value={formatDate(quote.created_at, true)} />
              <Row label="发送时间" value={quote.sent_at ? formatDate(quote.sent_at, true) : "尚未发送"} />
              <Row label="成交时间" value={quote.won_at ? formatDate(quote.won_at, true) : "—"} />
              {quote.confidence !== null ? (
                <Row label="识别置信度" value={formatPercent(quote.confidence, 0)} />
              ) : null}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>分享与查看</CardTitle>
              {quote.view_count > 0 ? <Badge tone="accent">{quote.view_count} 次查看</Badge> : null}
            </CardHeader>
            <CardContent className="space-y-3">
              {quote.public_url || publicUrl ? (
                <div className="rounded-xl border border-line bg-surface-2 p-3">
                  <p className="text-[11.5px] text-faint">公开报价链接</p>
                  <p className="mt-1 break-all font-mono text-[11.5px] text-ink-soft">{publicUrl ?? quote.public_url}</p>
                  <div className="mt-2.5 flex flex-wrap gap-2">
                    <Button size="sm" variant="secondary" onClick={() => void copy(publicUrl ?? quote.public_url ?? "", "链接")}>
                      <Copy className="h-3.5 w-3.5" />
                      复制链接
                    </Button>
                    <a href={(publicUrl ?? quote.public_url) ?? "#"} target="_blank" rel="noreferrer">
                      <Button size="sm" variant="ghost">
                        <ExternalLink className="h-3.5 w-3.5" />
                        预览
                      </Button>
                    </a>
                  </div>
                </div>
              ) : (
                <p className="text-[12.5px] text-muted">还没有公开链接，点击「发送给客户」即可生成。</p>
              )}
              {quote.view_count > 0 ? (
                <div className="space-y-1.5 text-[12.5px]">
                  <Row label="首次查看" value={quote.first_viewed_at ? formatDate(quote.first_viewed_at, true) : "—"} />
                  <Row label="最近查看" value={relativeTime(quote.last_viewed_at)} />
                </div>
              ) : null}
              {quote.missing_fields.length ? (
                <div className="rounded-xl border border-[#f6e0bd] bg-warning-soft px-3 py-2.5">
                  <p className="text-[12px] font-medium text-[#8a4b00]">待确认信息</p>
                  <p className="mt-1 text-[12px] text-[#8a4b00]">{quote.missing_fields.join(" · ")}</p>
                </div>
              ) : null}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>版本历史</CardTitle>
              <History className="h-4 w-4 text-faint" />
            </CardHeader>
            <CardContent>
              {versions.data?.versions?.length ? (
                <div className="space-y-2.5">
                  {versions.data.versions.map((version) => (
                    <div key={version.id} className="flex items-start justify-between gap-3 border-b border-line/70 pb-2.5 last:border-0">
                      <div>
                        <p className="text-[13px] font-medium text-ink">V{version.version_no}</p>
                        <p className="mt-0.5 text-[12px] text-faint">{version.change_note ?? "修改报价"}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[13px] tabular-nums text-ink">{formatCurrency(version.total_amount)}</p>
                        <p className="text-[11.5px] text-faint">{formatDate(version.created_at, true)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="暂无版本记录" className="py-8" />
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>操作审计</CardTitle>
            </CardHeader>
            <CardContent>
              {audit.data?.length ? (
                <div className="space-y-2.5">
                  {audit.data.slice(0, 8).map((entry) => (
                    <div key={entry.id} className="flex items-start gap-2.5">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                      <div>
                        <p className="text-[12.5px] text-ink-soft">{entry.summary ?? entry.action}</p>
                        <p className="text-[11.5px] text-faint">
                          {entry.user_name ?? "系统"} · {relativeTime(entry.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="暂无审计记录" className="py-8" />
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>危险操作</CardTitle>
            </CardHeader>
            <CardContent>
              <Button variant="dangerGhost" onClick={() => setVoidOpen(true)}>
                <Trash2 className="h-4 w-4" />
                作废这份报价
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
      <Dialog
        open={sendOpen}
        onClose={() => setSendOpen(false)}
        title="发送给客户"
        description="生成一条随机公开链接，客户无需登录即可查看"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setSendOpen(false)}>
              取消
            </Button>
            <Button loading={sending} onClick={() => void send()}>
              生成链接
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="报价有效期（天）" hint="到期后链接自动失效">
            <Input type="number" min={1} max={365} value={validDays} onChange={(event) => setValidDays(Number(event.target.value))} />
          </Field>
          <Field label="访问密码（可选）" hint="留空则任何人拿到链接都能查看">
            <Input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="例如 8888" />
          </Field>
          {publicUrl ? (
            <div className="rounded-xl border border-[#c8ecd7] bg-success-soft p-3">
              <p className="text-[12px] font-medium text-[#0b6b36]">链接已生成</p>
              <p className="mt-1 break-all font-mono text-[11.5px] text-[#0b6b36]">{publicUrl}</p>
              <Button size="sm" variant="secondary" className="mt-2" onClick={() => void copy(publicUrl, "链接")}>
                <Link2 className="h-3.5 w-3.5" />
                复制链接
              </Button>
            </div>
          ) : null}
        </div>
      </Dialog>
      <Dialog
        open={replyOpen}
        onClose={() => setReplyOpen(false)}
        title="生成客户回复"
        description="AI 生成文案，金额与报价单保持一致"
        footer={
          <>
            <Button variant="ghost" onClick={() => setReplyOpen(false)}>
              关闭
            </Button>
            <Button loading={aiLoading} onClick={() => void generateReply()}>
              生成
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="风格">
            <Select value={replyStyle} onChange={(event) => setReplyStyle(event.target.value)}>
              <option value="professional">专业版（推荐）</option>
              <option value="concise">简洁版</option>
              <option value="closing">成交版</option>
            </Select>
          </Field>
          {replyText ? (
            <div>
              <Textarea value={replyText} onChange={(event) => setReplyText(event.target.value)} className="min-h-[180px]" />
              <Button size="sm" variant="secondary" className="mt-2" onClick={() => void copy(replyText, "回复文案")}>
                <Copy className="h-3.5 w-3.5" />
                复制文案
              </Button>
            </div>
          ) : (
            <p className="text-[12.5px] text-muted">点击「生成」后，AI 会写一段可以直接发给客户的微信回复。</p>
          )}
        </div>
      </Dialog>
      <Dialog
        open={explainOpen}
        onClose={() => setExplainOpen(false)}
        title="报价解释"
        description="客户觉得贵时，生成专业且不暴露成本的说法"
        footer={
          <>
            <Button variant="ghost" onClick={() => setExplainOpen(false)}>
              关闭
            </Button>
            <Button loading={aiLoading} onClick={() => void generateExplain()}>
              生成解释
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="客户的疑问">
            <Input value={question} onChange={(event) => setQuestion(event.target.value)} />
          </Field>
          {explain ? (
            <div className="space-y-3">
              <div>
                <p className="text-[12.5px] font-medium text-ink">价格构成要点</p>
                <ul className="mt-2 space-y-1.5">
                  {explain.reasons.map((reason) => (
                    <li key={reason} className="flex gap-2 text-[12.5px] leading-relaxed text-muted">
                      <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <p className="text-[12.5px] font-medium text-ink">可直接发给客户</p>
                <p className="mt-1.5 whitespace-pre-wrap text-[12.5px] leading-relaxed text-ink-soft">{explain.customer_reply}</p>
                <Button size="sm" variant="secondary" className="mt-2" onClick={() => void copy(explain.customer_reply, "解释文案")}>
                  <Copy className="h-3.5 w-3.5" />
                  复制
                </Button>
              </div>
              {explain.adjust_options?.length ? (
                <div>
                  <p className="text-[12.5px] font-medium text-ink">可选降本方向</p>
                  <ul className="mt-2 space-y-1.5">
                    {explain.adjust_options.map((option) => (
                      <li key={option} className="flex gap-2 text-[12.5px] leading-relaxed text-muted">
                        <TrendingUp className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" />
                        {option}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="text-[12.5px] text-muted">AI 会从材料、工艺、人工、安装、售后等角度给出解释，不会暴露成本与利润率。</p>
          )}
        </div>
      </Dialog>
      <ConfirmDialog
        open={voidOpen}
        onClose={() => setVoidOpen(false)}
        title="确认作废这份报价？"
        description="作废后客户链接会失效，但历史数据与版本记录仍然保留。"
        confirmText="确认作废"
        danger
        onConfirm={async () => {
          try {
            await quoteApi.remove(quoteId);
            toast.success("报价已作废");
            setVoidOpen(false);
            router.push("/app/quotes");
          } catch (err) {
            toast.error(errorMessage(err));
          }
        }}
      />
    </div>
  );
}
function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted">{label}</span>
      <span className="text-right font-medium text-ink-soft">{value}</span>
    </div>
  );
}
function quoteToAiPayload(quote: Quote) {
  return {
    quote_no: quote.quote_no,
    project_name: quote.project_name,
    total_amount: quote.total_amount,
    items: quote.items.map((item) => ({
      product_name: item.product_name,
      unit: item.unit,
      quantity: item.quantity,
      final_price: item.final_price,
    })),
    tiers: quote.tiers,
  };
}
