import { useCallback, useEffect, useState } from "react";

import { getTaskAdoReferences } from "../services/azureDevOpsApi";
import type { AdoReference } from "../services/azureDevOpsApi";

export function useTaskAdoReferences(taskId: number | null) {
  const [references, setReferences] = useState<AdoReference[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (taskId === null) return;
    setIsLoading(true);
    try {
      setReferences(await getTaskAdoReferences(taskId));
    } catch {
      // Azure DevOps lookups failing must never make the rest of the Task unusable (FR-033).
      setReferences([]);
    } finally {
      setIsLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { references, isLoading, refresh };
}
