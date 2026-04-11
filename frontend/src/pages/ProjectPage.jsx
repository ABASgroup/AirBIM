// Страница проекта
import { useParams } from "react-router-dom";
import { getProject } from "@/api/project";
import { useState, useEffect } from "react";
import { FilledButton } from "@ui";
import { IfcViewerModal } from "@app/components/IfcViewerModal"

function ProjectPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    getProject(projectId)
      .then(res => setProject(res.data))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <div>Загрузка...</div>;

  return (
    <>
      <h1>{project?.name}</h1>
      <p>{project?.description}</p>
      <FilledButton onClick={() => setIsModalOpen(true)}>Показать BIM</FilledButton>
      <IfcViewerModal
        url="/ifc2x3_Myran.ifc"
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  )
}
export default ProjectPage;