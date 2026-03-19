import { createContext, useContext, useState, useEffect } from "react";
import { getWorkspaces } from "../api/workspace";

const WorkspaceContext = createContext();

export const WorkspaceProvider = ({ children }) => {
  const [workspaces, setWorkspaces] = useState([]);
  const [currentWorkspace, setCurrentWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getWorkspaces().then(res => {
      setWorkspaces(res.data);
      const savedId = localStorage.getItem("currentWorkspaceId");
      const personal = res.data.find(w => w.type === "personal");
      const target = savedId ? res.data.find(w => w.id === Number(savedId)) : personal;
      setCurrentWorkspace(target || res.data[0]);
      setLoading(false);
    });
  }, []);

  const switchWorkspace = (id) => {
    const ws = workspaces.find(w => w.id === id);
    if (ws) {
      setCurrentWorkspace(ws);
      localStorage.setItem("currentWorkspaceId", id);
    }
  };

  return (
    <WorkspaceContext.Provider value={{ workspaces, currentWorkspace, loading, switchWorkspace }}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => useContext(WorkspaceContext);