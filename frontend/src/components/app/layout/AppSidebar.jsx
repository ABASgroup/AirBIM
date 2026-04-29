// Sidebar приложения
import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Dropdown, FilledButton, ActionMenu } from "@ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { CreateWorkspaceForm } from "@app/components/CreateWorkspaceForm";
import { createWorkspace, getWorkspaces, deleteWorkspace } from "@/api/workspace";

export const AppSidebar = () => {
  const [activeMenuId, setActiveMenuId] = useState(null);
  const actionBtnRefs = useRef({});
  const [isCreateWorkspaceModalOpen, setIsCreateWorkspaceModalOpen] = useState(false);
  const { workspaces, currentWorkspace, switchWorkspace, setWorkspaces } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate()
  const handleSelect = (ws) => {
    switchWorkspace(ws.id);
    setIsOpen(false);
    setActiveMenuId(null);
    navigate("/app/dashboard");
  };
  const handleCreateWorkspace = async (name) => {
    await createWorkspace(name);
    const res = await getWorkspaces();
    setWorkspaces(res.data);
    setIsCreateWorkspaceModalOpen(false);
  };
  const handleDeleteWorkspace = async (id) => {
    await deleteWorkspace(id);
    const res = await getWorkspaces();
    setWorkspaces(res.data);
    setActiveMenuId(null);
  };

  return (
    <aside className="w-50 shrink-0 sticky top-0 h-screen border-border-color border-r-3 z-50">
      <div className="bg-surface/70 h-15 w-full border-border-color border-b-3">
        <Dropdown
          label={currentWorkspace?.name}
          isOpen={isOpen}
          onToggle={(open) => { setIsOpen(open); if (!open) setActiveMenuId(null) }}
          className="h-15 px-4"
        >
          {workspaces.map((ws) => (
            <div
              key={ws.id}
              onClick={() => handleSelect(ws)}
              className={`w-70 px-1 py-2 text-left cursor-pointer gap-2 flex items-center 
                select-none justify-between rounded-[5px] hover:bg-black/30
                ${currentWorkspace?.id === ws.id && "border-2 border-text-color/20"}`}
            >
              <div className="flex items-center gap-2 grow min-w-0 overflow-hidden">
                <i className={`fa-solid w-5 text-center pl-1 ${ws.type === "personal" ? "fa-user" : "fa-users"}`}></i>
                <div className="flex flex-col items-start min-w-0">
                  <span className="truncate">{ws.name}</span>
                  <span className="text-xs text-text-color/30">
                    {ws.type === "personal" ? "Ваше личное пространство" : "Командное пространство"}
                  </span>
                </div>
              </div>

              <button
                className="p-1" 
                ref={(el) => actionBtnRefs.current[ws.id] = el}
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveMenuId(activeMenuId === ws.id ? null : ws.id);
                }}>
                <i className="fa-solid fa-bars flex justify-center shrink-0 text-text-color transition-all active:scale-95 cursor-pointer hover:brightness-75"></i>
              </button>

              {activeMenuId === ws.id && (
                <ActionMenu
                  isOpen={true}
                  onClose={() => setActiveMenuId(null)}
                  buttonRef={{ current: actionBtnRefs.current[ws.id] }}
                >
                  <button onClick={() => handleDeleteWorkspace(ws.id)}>
                    <i className="fa-solid fa-trash"></i>
                    Удалить
                  </button>

                  <button onClick={() => {
                    setIsOpen(null);
                    setActiveMenuId(null);
                    navigate(`/app/workspace/${ws.id}`)
                  }}>
                    <i className="fa-solid fa-building"></i>
                    Управление
                  </button>
                </ActionMenu>
              )}
            </div>
          ))}
          <FilledButton className="mx-auto my-2" onClick={() => setIsCreateWorkspaceModalOpen(true)}>
            <i className="fa-solid fa-plus text-text-color"></i>
            Создать новое пространство
          </FilledButton>
        </Dropdown>
      </div>
      <CreateWorkspaceForm
        isOpen={isCreateWorkspaceModalOpen}
        onClose={() => setIsCreateWorkspaceModalOpen(false)}
        onCreate={handleCreateWorkspace}
      />
    </aside>
  );
};