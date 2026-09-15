import { useCallback, useEffect, useState } from "react";

import * as activityLogApi from "../services/activityLogApi";
import type { ActivityLogEntry } from "../services/activityLogApi";

export function useActivityLog() {
  const [entries, setEntries] = useState<ActivityLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await activityLogApi.getActivityLog();
      setEntries(result);
    } catch {
      setError("Unable to load the Activity Log.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { entries, isLoading, error, refresh };
}
