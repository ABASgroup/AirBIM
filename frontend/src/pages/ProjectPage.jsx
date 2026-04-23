// Страница проекта
import { useParams } from "react-router-dom";
import { getProject } from "@/api/project";
import { getBimDownloadLink } from "@/api/file"
import { useState, useEffect } from "react";
import { FilledButton } from "@ui";
import { IfcViewerModal } from "@app/components/IfcViewerModal"
import { useToast } from "@/context/ToastContext";

function ProjectPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [bimUrl, setBimUrl] = useState(null);
  const [bimLoading, setBimLoading] = useState(false);
  const [bimError, setBimError] = useState(null);
  const { showToast } = useToast();

  useEffect(() => {
    getProject(projectId)
      .then(res => setProject(res.data))
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

  return (
    <>
      <h1>{project?.name}</h1>
      <p>{project?.description}</p>
      <FilledButton onClick={handleShowBim} disabled={bimLoading}>Показать BIM</FilledButton>
      {bimError && <p style={{ color: "red" }}>{bimError}</p>}
      <IfcViewerModal
        url={bimUrl}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  )
}
export default ProjectPage;