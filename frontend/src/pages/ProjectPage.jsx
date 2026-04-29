// Страница проекта
import { Link, useParams } from "react-router-dom";
import { getProject } from "@/api/project";
import { getWorkspace } from "@/api/workspace";
import { getBimDownloadLink } from "@/api/file";
import { useState, useEffect } from "react";
import { FilledButton, LoadingSpinner } from "@ui";
import { IfcViewerDrawer } from "@app/components/IfcViewerDrawer";
import { useToast } from "@/context/ToastContext";
import { useWorkspace } from "@/context/WorkspaceContext";

function ProjectPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [workspace, setWorkspace] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [bimUrl, setBimUrl] = useState(null);
  const [bimLoading, setBimLoading] = useState(false);
  const [bimError, setBimError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const { switchWorkspace } = useWorkspace();
  const { showToast } = useToast();

  useEffect(() => {
    setIsLoading(true);

    getProject(projectId)
      .then(res => {
        setProject(res.data);
        return getWorkspace(res.data.workspace_id);
      })
      .then(wsRes => setWorkspace(wsRes.data))
      .catch(() => setWorkspace(null))
      .finally(() => setIsLoading(false));
  }, [projectId]);

  const handleShowBim = async () => {
    setBimLoading(true);

    try {
      const response = await getBimDownloadLink(projectId);
      setBimUrl(response.data.url);
      setIsModalOpen(true);
    } catch (error) {
      if (error.response?.status === 404) {
        showToast({
          type: "warning",
          title: "Файл не найден",
          message: "BIM файл не загружен для этого проекта"
        });
      } else {
        showToast({
          type: "warning",
          title: "Ошибка",
          message: "Не удалось загрузить BIM файл"
        });
      }
    } finally {
      setBimLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner variant="inline" message="Загрузка проекта..." />;
  }

  return (
    <>
      <nav className="mb-4 flex flex-wrap items-center gap-2 text-sm text-text-color/70">
        {workspace && (
          <Link 
            to="/app/dashboard" 
            className="hover:underline"
            onClick={() => workspace && switchWorkspace(workspace.id)}
          >
            <h1>{workspace.name}</h1>
          </Link>
        )}
        <h1>/</h1>
        <h1 className="text-primary-color">{project?.name}</h1>
      </nav>

      <p>{project?.description}</p>
      <FilledButton onClick={handleShowBim} disabled={bimLoading}>Показать BIM</FilledButton>
      {bimError && <p style={{ color: "red" }}>{bimError}</p>}
      <IfcViewerDrawer
        url={bimUrl}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  )
}
export default ProjectPage;