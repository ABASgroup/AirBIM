// Контекст для управлением состояния воркспейсов во всем приложении
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getWorkspaces, getWorkspaceAccess } from "@/api/workspace";

const WorkspaceContext = createContext();

export const WorkspaceProvider = ({ children }) => {
  const [workspaces, setWorkspaces] = useState([]);
  const [currentWorkspace, setCurrentWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [permissions, setPermissions] = useState([]);
  const [loadingPermissions, setLoadingPermissions] = useState(true);

  useEffect(() => {
    getWorkspaces().then(res => {
      setWorkspaces(res.data);
      const savedId = localStorage.getItem("currentWorkspaceId");
      const personal = res.data.find(w => w.type === "personal");
      const target = savedId ? res.data.find(w => w.id === savedId) : personal;
      setCurrentWorkspace(target || res.data[0]);
      setLoading(false);
    });
  }, []);

  const switchWorkspace = useCallback((id) => {
    const ws = workspaces.find(w => w.id === id);
    if (ws) {
      setCurrentWorkspace(ws);
      localStorage.setItem("currentWorkspaceId", id);
    }
  }, [workspaces]);

  useEffect(() => {
    if (!currentWorkspace?.id) return;

    setLoadingPermissions(true);
    getWorkspaceAccess(currentWorkspace.id)
      .then(res => {
        setPermissions(res.data.permissions);
      })
      .catch(err => {
        setPermissions([]);
      })
      .finally(() => {
        setLoadingPermissions(false);
      });
  }, [currentWorkspace?.id]);

  const hasPermission = useCallback((permissionKeys) => {
    if (Array.isArray(permissionKeys)) {
      return permissionKeys.every(key => permissions.includes(key));
    }
    return permissions.includes(permissionKeys);
  }, [permissions]);

  return (
    <WorkspaceContext.Provider value={{
      workspaces,
      setWorkspaces,
      currentWorkspace,
      loading,
      switchWorkspace,
      permissions,
      hasPermission,
      loadingPermissions
    }}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => useContext(WorkspaceContext);