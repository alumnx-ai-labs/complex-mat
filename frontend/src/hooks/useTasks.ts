import { useCallback, useEffect, useState } from "react";

import * as tasksApi from "../services/tasksApi";
import type { TaskStatus, TaskWithMeeting } from "../services/tasksApi";
import type { TaskCreateInput, TaskUpdateInput } from "../services/tasksApi";

export function useTasks(meetingId: number, onChange: () => void | Promise<void>) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const createTask = useCallback(async (input: TaskCreateInput) => {
    setIsSubmitting(true);
    try {
      const task = await tasksApi.createTask(meetingId, input);
      await onChange();
      return task;
    } finally {
      setIsSubmitting(false);
    }
  }, [meetingId, onChange]);

  const updateTask = useCallback(async (taskId: number, input: TaskUpdateInput) => {
    setIsSubmitting(true);
    try {
      const task = await tasksApi.updateTask(taskId, input);
      await onChange();
      return task;
    } finally {
      setIsSubmitting(false);
    }
  }, [onChange]);

  const updateStatus = useCallback(async (taskId: number, status: TaskStatus) => {
    setIsSubmitting(true);
    try {
      const task = await tasksApi.updateTaskStatus(taskId, status);
      await onChange();
      return task;
    } finally {
      setIsSubmitting(false);
    }
  }, [onChange]);

  const deleteTask = useCallback(async (taskId: number) => {
    setIsSubmitting(true);
    try {
      await tasksApi.deleteTask(taskId);
      await onChange();
    } finally {
      setIsSubmitting(false);
    }
  }, [onChange]);

  return { createTask, updateTask, updateStatus, deleteTask, isSubmitting };
}

export function useMyTasks() {
  const [tasks, setTasks] = useState<TaskWithMeeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await tasksApi.listMyTasks();
      setTasks(result);
    } catch {
      setError("Unable to load your tasks.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const updateStatus = useCallback(
    async (taskId: number, status: TaskStatus) => {
      await tasksApi.updateTaskStatus(taskId, status);
      await refresh();
    },
    [refresh],
  );

  const updateDescription = useCallback(
    async (taskId: number, descriptionNotes: string) => {
      await tasksApi.updateTaskDescription(taskId, descriptionNotes);
      await refresh();
    },
    [refresh],
  );

  return { tasks, isLoading, error, refresh, updateStatus, updateDescription };
}
