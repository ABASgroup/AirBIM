// Контекст прогрессбара задач
import { createContext, useContext, useState, useEffect, useRef } from "react";
import { getActiveTasks, getWorkspaceTasks } from "@/api/task";
import { getTaskTypeLabel } from "@/utils/taskLabels";
import { useToast } from "./ToastContext";
import { useWorkspace } from "./WorkspaceContext";

const TaskProgressContext = createContext();

export const useTaskProgress = () => useContext(TaskProgressContext);

const POLL_INTERVAL_MS = 3000;
const ACTIVE_STATUSES = new Set(["pending", "started"]);

export const TaskProgressProvider = ({ children }) => {
  const [activeTasks, setActiveTasks] = useState([]);
  const { showToast } = useToast();
  const { currentWorkspace } = useWorkspace();
  const prevActiveRef = useRef(new Map());
  const notifiedRef = useRef(new Set());
  const showToastRef = useRef(showToast);

  useEffect(() => {
    showToastRef.current = showToast;
  }, [showToast]);

  useEffect(() => {
    if (!currentWorkspace?.id) {
      setActiveTasks([]);
      prevActiveRef.current = new Map();
      return;
    }

    const workspaceId = currentWorkspace.id;
    prevActiveRef.current = new Map();
    notifiedRef.current = new Set();

    const poll = async () => {
      try {
        const { data } = await getActiveTasks(workspaceId);
        const newActive = data.filter((task) => ACTIVE_STATUSES.has(task.status));
        const newActiveMap = new Map(newActive.map((task) => [task.id, task]));

        const disappeared = [];
        for (const [id, task] of prevActiveRef.current) {
          if (!newActiveMap.has(id)) {
            disappeared.push(task);
          }
        }

        if (disappeared.length > 0) {
          const { data: allTasks } = await getWorkspaceTasks(workspaceId);

          for (const oldTask of disappeared) {
            if (notifiedRef.current.has(oldTask.id)) continue;

            const finalTask = allTasks.find((t) => t.id === oldTask.id);
            if (!finalTask) continue;

            const taskLabel = getTaskTypeLabel(oldTask.type);
            const taskEntityId = finalTask.entity_id || oldTask.id;
            if (finalTask.status === "succeeded") {
              showToastRef.current({
                type: "primary",
                title: "Задача завершена",
                message: `«${taskLabel}» успешно выполнена: ${taskEntityId}`,
              });
            } else if (finalTask.status === "failed") {
              showToastRef.current({
                type: "warning",
                title: "Ошибка задачи",
                message: `«${taskLabel}» завершилась с ошибкой: ${taskEntityId}`,
              });
            }

            notifiedRef.current.add(oldTask.id);
          }
        }

        prevActiveRef.current = newActiveMap;
        setActiveTasks(newActive);
      } catch {
      }
    };

    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [currentWorkspace?.id]);

  return (
    <TaskProgressContext.Provider value={{ activeTasks }}>
      {children}
    </TaskProgressContext.Provider>
  );
};
