import { useState } from "react";
import { Dropdown } from "./Dropdown";
import { useWorkspace } from "../context/WorkspaceContext";
import { FilledButton } from "./FilledButton";

export const AppSidebar = () => {
  const { workspaces, currentWorkspace, switchWorkspace } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const handleSelect = (ws) => {
    switchWorkspace(ws.id);
    setIsOpen(false);
  };

  const trigger = (
    <div className="h-15 px-4 flex items-center justify-between cursor-pointer border-border-color border-b-3">
      <span className="truncate">{currentWorkspace?.name || "Загрузка..."}</span>
      <i className={`fa-solid fa-chevron-down transition-transform ${isOpen ? "rotate-180" : ""}`}></i>
    </div>
  );

  return (
    <aside className="w-50 shrink-0 sticky top-0 h-screen border-border-color border-r-3">
      <div className="bg-surface/70 h-15 w-full border-border-color border-b-3">
        <Dropdown trigger={trigger} isOpen={isOpen} onToggle={setIsOpen}>
          {workspaces.map((ws) => (
            <button
              key={ws.id}
              onClick={() => handleSelect(ws)}
              className={`w-100 px-4 py-2 text-left cursor-pointer flex items-center gap-2 border-none select-none 
                ${currentWorkspace?.id === ws.id ? "bg-mute-text-color rounded-[5px]" : "bg-transparent"
                }`}
            >
              <i className={`fa-solid w-5 text-center ${ws.type === "personal" ? "fa-user" : "fa-users"}`}></i>
              <div className="flex flex-col items-start min-w-0">
                <span className="truncate">{ws.name}</span>
                <span className="text-xs text-text-color/30">
                  {ws.type === "personal" ? "Ваше личное пространство" : "Командное пространство"}
                </span>
              </div>
            </button>
          ))}
          <FilledButton className="mx-auto my-2">
            <i className="fa-solid fa-plus text-text-color"></i>
            Создать новое пространство
          </FilledButton>
        </Dropdown>
      </div>
    </aside>
  );
};