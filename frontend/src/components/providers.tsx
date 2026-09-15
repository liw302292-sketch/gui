"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

import { authApi, errorMessage } from "@/lib/api";
import type { MeResponse } from "@/lib/types";
import { Toaster, toast } from "@/components/ui/toast";

interface SessionContextValue {
  session: MeResponse | null;
  loading: boolean;
  refresh: () => Promise<MeResponse | null>;
  logout: () => Promise<void>;
  isAdmin: boolean;
}

const SessionContext = React.createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [session, setSession] = React.useState<MeResponse | null>(null);
  const [loading, setLoading] = React.useState(true);

  const refresh = React.useCallback(async () => {
    try {
      const me = await authApi.me();
      setSession(me);
      return me;
    } catch {
      setSession(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = React.useCallback(async () => {
    try {
      await authApi.logout();
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setSession(null);
      router.push("/login");
    }
  }, [router]);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = React.useMemo<SessionContextValue>(
    () => ({ session, loading, refresh, logout, isAdmin: Boolean(session?.user.is_superadmin) }),
    [session, loading, refresh, logout],
  );

  return (
    <SessionContext.Provider value={value}>
      {children}
      <Toaster />
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const context = React.useContext(SessionContext);
  if (!context) throw new Error("useSession 必须在 SessionProvider 内使用");
  return context;
}

