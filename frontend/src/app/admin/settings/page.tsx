"use client";
import { Save, Settings } from "lucide-react";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input } from "@/components/ui/input";
import { ErrorState, SkeletonRows } from "@/components/ui/states";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { adminApi, errorMessage } from "@/lib/api";
export default function AdminSettingsPage() {
  const { data, loading, error, reload } = useApiData(() => adminApi.settings(), []);
  const [key, setKey] = React.useState("platform.notice");
  const [value, setValue] = React.useState('{\n  "text": ""\n}');
  const [saving, setSaving] = React.useState(false);
  async function save() {
    let parsed: Record<string, unknown> = {};
    try {
      parsed = JSON.parse(value);
    } catch {
      toast.error("值必须是合法 JSON");
      return;
    }
    setSaving(true);
    try {
      await adminApi.saveSetting(key, parsed);
      toast.success("设置已保存");
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }
  return (
    <div>
      <PageHeader title="系统设置" description="运行期配置、行业模板与 Prompt 文件" />
      {loading ? (
        <SkeletonRows rows={5} />
      ) : error || !data ? (
        <ErrorState message={error ?? "加载失败"} onRetry={reload} />
      ) : (
        <div className="grid gap-4 xl:grid-cols-[1.3fr_1fr]">
          <Card>
            <CardHeader>
              <CardTitle>运行期配置</CardTitle>
              <Badge tone="neutral">来自环境变量</Badge>
            </CardHeader>
            <CardContent className="space-y-2.5 text-[13px]">
              {Object.entries(data.runtime).map(([name, item]) => (
                <div key={name} className="flex items-center justify-between border-b border-line/70 pb-2 last:border-0">
                  <span className="font-mono text-[12px] text-muted">{name}</span>
                  <span className="font-medium text-ink">{String(item)}</span>
                </div>
              ))}
            </CardContent>
          </Card>
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>行业模板</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {data.industries.map((industry) => (
                  <div
                    key={industry.code}
                    className="flex items-center justify-between rounded-xl border border-line px-3.5 py-2.5"
                  >
                    <div>
                      <p className="text-[13px] font-medium text-ink">{industry.name}</p>
                      <p className="text-[11.5px] text-faint">{industry.description}</p>
                    </div>
                    <Badge tone={industry.status === "available" ? "success" : "neutral"}>
                      {industry.status === "available" ? "已上线" : "即将上线"}
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Prompt 文件</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {data.prompt_files.map((file) => (
                  <div key={file.name} className="flex items-center justify-between text-[12.5px]">
                    <span className="font-mono text-muted">{file.name}</span>
                    <span className="text-faint">{file.size} B</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
          <Card className="xl:col-span-2">
            <CardHeader>
              <CardTitle>自定义系统设置</CardTitle>
              <Settings className="h-4 w-4 text-faint" />
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-[240px_1fr]">
              <Field label="设置项 Key">
                <Input value={key} onChange={(event) => setKey(event.target.value)} />
              </Field>
              <Field label="值（JSON）">
                <textarea
                  value={value}
                  onChange={(event) => setValue(event.target.value)}
                  className="min-h-[110px] w-full rounded-xl border border-line-strong bg-surface px-3.5 py-2.5 font-mono text-[12px]"
                />
              </Field>
              <div className="sm:col-span-2">
                <Button loading={saving} onClick={() => void save()}>
                  <Save className="h-4 w-4" />
                  保存设置
                </Button>
                <p className="mt-2 text-[12px] text-faint">
                  已保存的设置项：{Object.keys(data.stored).length ? Object.keys(data.stored).join("、") : "暂无"}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

