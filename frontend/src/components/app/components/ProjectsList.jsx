import { useState, useRef, useEffect } from "react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { getProjects, createProject, deleteProject, updateProject } from "@/api/project";
import { FilledButton } from "@ui/FilledButton";
import { ActionMenu } from "@ui/ActionMenu";
import { ProjectModal } from "./ProjectModal";

export const ProjectsList = () => {
  const { currentWorkspace } = useWorkspace();
  const [projects, setProjects] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [activeMenuId, setActiveMenuId] = useState(null);
  const actionBtnRefs = useRef({});
  useEffect(() => {
    setProjects([]);
    if (currentWorkspace?.id) {
      getProjects(currentWorkspace.id).then(res => setProjects(res.data));
    }
  }, [currentWorkspace?.id]);
  const handleCreate = async (data) => {
    await createProject(currentWorkspace.id, data);
    const res = await getProjects(currentWorkspace.id);
    setProjects(res.data);
    setIsModalOpen(false);
  };
  const handleDelete = async (projectId) => {
    await deleteProject(projectId);
    const res = await getProjects(currentWorkspace.id);
    setProjects(res.data);
    setActiveMenuId(null);
  };
  const handleUpdate = async (data) => {
    await updateProject(editingProject.id, data);
    const res = await getProjects(currentWorkspace.id);
    setProjects(res.data);
    setEditModalOpen(false);
    setEditingProject(null);
  };
  const openEditModal = (project) => {
    setEditingProject(project);
    setEditModalOpen(true);
    setActiveMenuId(null);
  };
  const isEmpty = !projects || projects.length === 0;

  return (
    <div>
      {isEmpty ? (
        <div className="flex flex-col items-center justify-center py-20 gap-5">
          <p>Создайте первый проект</p>
          <FilledButton onClick={() => setIsModalOpen(true)}>
            <i className="fa-solid fa-plus text-text-color"></i> Создать проект
          </FilledButton>
        </div>
      ) : (
        <>
          <div className="flex justify-between items-center mb-4">
            <FilledButton onClick={() => setIsModalOpen(true)}>
              <i className="fa-solid fa-plus text-text-color"></i> Создать проект
            </FilledButton>
          </div>
        </>
      )}
      <div className="grid gap-3">
        {projects.map((project) => (
          <div key={project.id} className="flex items-center justify-between rounded-[5px] p-5 bg-surface">
            <div>
              <h3 className="font-bold">{project.name}</h3>
              {project.description ? (
                <p className="text-text-color">{project.description}</p>
              ) : (
                <p className="text-mute-text-color">Описание отсутствует</p>
              )}

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
                    onClick={() => openEditModal(project)}
                  >
                    <i className="fa-solid fa-pen"></i>
                    Редактировать
                  </button>
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
      <ProjectModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreate}
        mode="create"
        workspaceId={currentWorkspace?.id}
      />
      <ProjectModal
        isOpen={editModalOpen}
        onClose={() => { setEditModalOpen(false); setEditingProject(null); }}
        onSubmit={handleUpdate}
        mode="edit"
        project={editingProject}
      />
    </div>
  );
};