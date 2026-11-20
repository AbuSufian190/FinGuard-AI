import { useCallback, useEffect, useState } from "react";

interface State<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/** Minimal data-fetching hook with loading/error state and manual refetch. */
export function useFetch<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<State<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const run = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    fn()
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((e) =>
        setState({
          data: null,
          loading: false,
          error:
            e?.response?.data?.detail ||
            e?.message ||
            "Request failed. Is the backend running?",
        })
      );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(run, [run]);

  return { ...state, refetch: run };
}
