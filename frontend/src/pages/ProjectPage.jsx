// Страница проекта
import { Link, useParams } from "react-router-dom";
import { getProject } from "@/api/project";
import { getWorkspace } from "@/api/workspace";
import { useState, useEffect } from "react";
import { FilledButton, UnfilledButton, LoadingSpinner } from "@ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { StageUploadModal, StagesAccordion } from "@app/components";

function ProjectPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [workspace, setWorkspace] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const { switchWorkspace } = useWorkspace();
  const [showStageModal, setShowStageModal] = useState(false);
  const [stageUploadVersion, setStageUploadVersion] = useState(0);

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

      <div className="flex gap-3 mt-5">
        <Link to={`/app/projects/${projectId}/scene`}>
          <FilledButton>
            Перейти к сцене
          </FilledButton>
        </Link>

        <UnfilledButton onClick={() => setShowStageModal(true)}>
          Загрузить этап
        </UnfilledButton>

        <Link to={`/app/projects/${projectId}/results`}>
          <FilledButton>
            Перейти к результатам
          </FilledButton>
        </Link>
      </div>


      <div className="mt-6">
        <StagesAccordion key={stageUploadVersion} projectId={projectId} />
      </div>

      {showStageModal && (
        <StageUploadModal
          projectId={projectId}
          onClose={() => setShowStageModal(false)}
          onSuccess={() => setStageUploadVersion(v => v + 1)}
        />
      )}
    </>
  )
}
export default ProjectPage;