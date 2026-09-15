"use client";
import { Search, Users } from "lucide-react";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { adminApi, errorMessage } from "@/lib/api";
import { formatDate } from "@/lib/utils";
export default function AdminUsersPage() {
  const [keyword, setKeyword] = React.useState("");
  const [search, setSearch] = React.useState("");
  const { data, loading, error, reload } = useApiData(
    () => adminApi.users({ keyword: search || undefined, page_size: 50 }),
    [search],
  );
  React.useEffect(() => {
    const timer = window.setTimeout(() => setSearch(keyword.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [keyword]);
  async function toggle(userId: number, status: string) {
    try {
      await adminApi.setUserStatus(userId, status === "active" ? "disabled" : "active");
      toast.success("用户状态已更新");
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }
  return (
    <div>
      <PageHeader
        title="用户管理"
        description="平台所有注册用户与登录状态"
        actions={
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-faint" />
            <Input
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="搜索姓名 / 邮箱 / 手机号"
              className="w-64 pl-9"
            />
          </div>
        }
      />
      <Card>
        <CardContent className="pt-5">
          {loading ? (
            <SkeletonRows rows={6} />
          ) : error ? (
            <ErrorState message={error} onRetry={reload} />
          ) : !data?.items.length ? (
            <EmptyState icon={<Users className="h-5 w-5" />} title="暂无用户" />
          ) : (
            <Table>
              <THead>
                <Th>用户</Th>
                <Th>邮箱</Th>
                <Th>手机号</Th>
                <Th className="text-right">所属企业</Th>
                <Th>注册时间</Th>
                <Th>最近登录</Th>
                <Th>状态</Th>
                <Th />
              </THead>
              <TBody>
                {data.items.map((user) => (
                  <Tr key={user.id}>
                    <Td>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-ink">{user.name}</span>
                        {user.is_superadmin ? <Badge tone="dark">管理员</Badge> : null}
                      </div>
                    </Td>
                    <Td className="text-muted">{user.email ?? "—"}</Td>
                    <Td className="text-muted">{user.phone ?? "—"}</Td>
                    <Td className="text-right tabular-nums">{user.company_count}</Td>
                    <Td className="text-[12px] text-muted">{formatDate(user.created_at)}</Td>
                    <Td className="text-[12px] text-muted">{user.last_login_at ? formatDate(user.last_login_at, true) : "从未登录"}</Td>
                    <Td>
                      <StatusBadge status={user.status} label={user.status === "active" ? "正常" : "已禁用"} />
                    </Td>
                    <Td className="text-right">
                      {user.is_superadmin ? null : (
                        <Button variant="ghost" size="sm" onClick={() => void toggle(user.id, user.status)}>
                          {user.status === "active" ? "禁用" : "启用"}
                        </Button>
                      )}
                    </Td>
                  </Tr>
                ))}
              </TBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

