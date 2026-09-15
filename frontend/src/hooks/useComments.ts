import { useCallback, useEffect, useState } from "react";

import * as commentsApi from "../services/commentsApi";
import type { Comment } from "../services/commentsApi";

export function useComments(taskId: number | null) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (taskId === null) return;
    setIsLoading(true);
    setError(null);
    try {
      setComments(await commentsApi.listComments(taskId));
    } catch {
      setError("Unable to load comments.");
    } finally {
      setIsLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const postComment = useCallback(
    async (message: string) => {
      if (taskId === null) return;
      await commentsApi.postComment(taskId, message);
      await refresh();
    },
    [taskId, refresh],
  );

  return { comments, isLoading, error, postComment, refresh };
}
