// Список проектов на дашборде
import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useWorkspace } from "@/context/WorkspaceContext";
import { getProjects, createProject, deleteProject, updateProject } from "@/api/project";
import { getBimUploadLink, uploadFileWithPresignedLink, confirmBimUpload } from "@/api/file";
import { isIFC } from "@utils";
import { FilledButton, ActionMenu, LoadingSpinner } from "@ui";
import { ProjectModal, Can } from "@app/components";

export const ProjectsList = () => {
  const { currentWorkspace } = useWorkspace();
  const [projects, setProjects] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [activeMenuId, setActiveMenuId] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const actionBtnRefs = useRef({});
  const navigate = useNavigate();
  useEffect(() => {
    setProjects([]);
    setIsLoading(true);
    if (currentWorkspace?.id) {
      getProjects(currentWorkspace.id)
        .then(res => setProjects(res.data))
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [currentWorkspace?.id]);

  const uploadProjectFile = async (projectId, file) => {
    try {
      setIsUploading(true);
      const uploadLink = await getBimUploadLink(projectId, {
        filename: file.name,
        size: file.size,
        content_type: isIFC(file) ? "application/x-step" : file.type,
      });

      const presignedUrl = uploadLink.data.url;
      const confirmData = {
        filename: uploadLink.data.file.filename,
        size: uploadLink.data.file.size,
        content_type: uploadLink.data.file.content_type
      };

      await uploadFileWithPresignedLink(presignedUrl, file);
      await confirmBimUpload(uploadLink.data.file.id, confirmData);

      return { success: true };
    } catch (error) {
      console.error("File upload failed:", error);
      return { success: false, error };
    } finally {
      setIsUploading(false);
    }
  };

  const handleCreate = async (data) => {
    try {
      const { file, ...projectData } = data;

      const projectRes = await createProject(currentWorkspace.id, projectData);
      const projectId = projectRes.data.id;

      if (file) {
        await uploadProjectFile(projectId, file);
      }
    } catch (error) {
      console.error("Project creation failed:", error);
    }

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

  if (isLoading) {
    return <LoadingSpinner variant="inline" message="Загрузка проектов..." />;
  }

  return (
    <div>
      {(!projects || projects.length === 0) ? (
        <div className="flex flex-col items-center justify-center py-20 gap-5">
          <p>Проекты отсутствуют</p>
          <Can permission="projects:create">
            <FilledButton onClick={() => setIsModalOpen(true)}>
              <i className="fa-solid fa-plus text-text-color"></i> Создать проект
            </FilledButton>
          </Can>
        </div>
      ) : (
        <>
          <div className="flex justify-between items-center mb-4">
            <Can permission="projects:create">
              <FilledButton onClick={() => setIsModalOpen(true)}>
                <i className="fa-solid fa-plus text-text-color"></i> Создать проект
              </FilledButton>
            </Can>
          </div>
        </>
      )}
      <div className="grid gap-3">
        {projects.map((project) => (
          <div
            key={project.id}
            className="flex items-center justify-between rounded-[5px] p-5 bg-surface cursor-pointer shadow-bottom"
            onClick={() => navigate(`/app/projects/${project.id}`)}>
            <div>
              <h3 className="font-bold">{project.name}</h3>
              {project.description ? (
                <p className="text-text-color">{project.description}</p>
              ) : (
                <p className="text-mute-text-color">Описание отсутствует</p>
              )}
            </div>
            <div>
              <Can permissions={["projects:edit", "projects:delete"]}>
                <button
                  ref={(el) => actionBtnRefs.current[project.id] = el}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveMenuId(activeMenuId === project.id ? null : project.id);
                  }}
                >
                  <i className="fa-solid fa-bars text-text-color p-2 transition-all active:scale-95 cursor-pointer hover:brightness-75"></i>
                </button>
              </Can>
              {activeMenuId === project.id && (
                <ActionMenu
                  isOpen={true}
                  onClose={() => setActiveMenuId(null)}
                  buttonRef={{ current: actionBtnRefs.current[project.id] }}
                >
                  <button onClick={() => openEditModal(project)} >
                    <i className="fa-solid fa-pen"></i>
                    Редактировать
                  </button>
                  <button onClick={() => handleDelete(project.id)}>
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