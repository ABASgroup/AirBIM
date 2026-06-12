import api from "./index";

const serializeParams = (params) => {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (Array.isArray(value)) {
      value.forEach((item) => searchParams.append(key, item));
    } else if (value != null) {
      searchParams.append(key, value);
    }
  }
  return searchParams.toString();
};

const ACTIVE_STATUSES = ["pending", "started"];

export const getWorkspaceTasks = (workspaceId) =>
  api.get(`/workspaces/${workspaceId}/tasks`);

export const getActiveTasks = (workspaceId) =>
  api.get(`/workspaces/${workspaceId}/tasks`, {
    params: { statuses: ACTIVE_STATUSES },
    paramsSerializer: serializeParams,
  });