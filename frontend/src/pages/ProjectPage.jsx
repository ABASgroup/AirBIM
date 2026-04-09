// Страница проекта
import { useParams } from "react-router-dom";
import { getProject } from "@/api/project";
import { useState, useEffect } from "react";

function ProjectPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);

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
    </>
  )
}
export default ProjectPage;