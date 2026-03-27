import { useState, useRef, useEffect } from "react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { getProjects, createProject, deleteProject } from "@/api/project";
import { FilledButton } from "@ui/FilledButton";
import { ActionMenu } from "@ui/ActionMenu";
import { CreateProjectModal } from "./CreateProjectModal";

export const ProjectsList = () => {
  const { currentWorkspace } = useWorkspace();
  const [projects, setProjects] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState(null);
  const actionBtnRefs = useRef({});
  useEffect(() => {
    setProjects([]);
    if (currentWorkspace?.id) {
      getProjects(currentWorkspace.id).then(res => setProjects(res.data));
    }
  }, [currentWorkspace?.id]);
  const handleCreate = async (data) => {
    await createProject(data);
    const res = await getProjects(currentWorkspace.id);
    setProjects(res.data);
    setIsModalOpen(false);
  };
  const handleDelete = async (projectId) => {
    await deleteProject(currentWorkspace.id, projectId);
    const res = await getProjects(currentWorkspace.id);
    setProjects(res.data);
    setActiveMenuId(null);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <FilledButton onClick={() => setIsModalOpen(true)}>
          <i className="fa-solid fa-plus text-text-color"></i> Создать проект
        </FilledButton>
      </div>
      <div className="grid gap-4">
        {projects.map((project) => (
          <div key={project.id} className="flex items-center justify-between rounded-[5px] p-5 bg-surface">
            <div>
              <h3 className="font-bold">{project.name}</h3>
              <p className="text-text-color">{project.description}</p>
            </div>
            
            <div>
              <button
                ref={(el) => actionBtnRefs.current[project.id] = el}
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveMenuId(activeMenuId === project.id ? null : project.id);
                }}
              >
                <i className="fa-solid fa-bars text-text-color p-2"></i>
              </button>
              
              {activeMenuId === project.id && (
                <ActionMenu
                  isOpen={true}
                  onClose={() => setActiveMenuId(null)}
                  buttonRef={{ current: actionBtnRefs.current[project.id] }}
                >
                  <button
                    className="w-full px-4 py-2 text-left hover:bg-mute-text-color flex items-center gap-2"
                    onClick={() => handleDelete(project.id)}
                  >
                    <i className="fa-solid fa-trash"></i>
                    Удалить
                  </button>
                </ActionMenu>
              )}
            </div>
          </div>
        ))}
      </div>
      <CreateProjectModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreate={handleCreate}
        workspaceId={currentWorkspace?.id}
      />
    </div>
  );
};