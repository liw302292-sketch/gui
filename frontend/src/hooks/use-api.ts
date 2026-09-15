"use client";

import * as React from "react";

import { ApiError, errorMessage } from "@/lib/api";

interface State<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  unauthorized: boolean;
}

/** 通用数据加载 Hook：统一 loading / error / unauthorized 处理。 */
export function useApiData<T>(loader: () => Promise<T>, deps: unknown[] = []): State<T> & { reload: () => void } {
  const [state, setState] = React.useState<State<T>>({
    data: null,
    loading: true,
    error: null,
    unauthorized: false,
  });
  const [tick, setTick] = React.useState(0);
  const loaderRef = React.useRef(loader);
  loaderRef.current = loader;

  React.useEffect(() => {
    let cancelled = false;
    setState((prev) => ({ ...prev, loading: true, error: null }));
    loaderRef
      .current()
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null, unauthorized: false });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          data: null,
          loading: false,
          error: errorMessage(error),
          unauthorized: error instanceof ApiError && error.status === 401,
        });
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  const reload = React.useCallback(() => setTick((value) => value + 1), []);
  return { ...state, reload };
}

