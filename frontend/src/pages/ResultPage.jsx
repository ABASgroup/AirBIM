// Страница результатов (отчетов)
import { Link, useParams } from "react-router-dom";
import { getProject } from "@/api/project";
import { getWorkspace } from "@/api/workspace";
import { getProjectResults, getFileDownloadLink } from "@/api/recordingResult";
import { useState, useEffect } from "react";
import { LoadingSpinner, Accordion, FilledButton, UnfilledButton } from "@ui";
import { useWorkspace } from "@/context/WorkspaceContext";

function ResultPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [workspace, setWorkspace] = useState(null);
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const { switchWorkspace } = useWorkspace();

  useEffect(() => {
    setIsLoading(true);

    getProject(projectId)
      .then(res => {
        setProject(res.data);
        return Promise.all([getWorkspace(res.data.workspace_id), getProjectResults(projectId)]);
      })
      .then(([wsRes, resultsRes]) => {
        setWorkspace(wsRes.data);
        setResults(resultsRes.data || []);
      })
      .catch(() => setWorkspace(null))
      .finally(() => setIsLoading(false));
  }, [projectId]);

  if (isLoading) {
    return <LoadingSpinner variant="inline" message="Загрузка результатов..." />;
  }

  const planFactResults = results.filter((result) => result.type === "plan_fact");
  const workFixationResults = results.filter((result) => result.type === "progress");
  const hasAnyResults = results.length > 0;

  const handleDownloadReport = async (fileId) => {
    try {
      const res = await getFileDownloadLink(fileId);
      const url = res?.data?.url;
      if (url) {
        window.open(url, "_blank");
      }
    } catch {
      console.error("Не удалось получить ссылку для скачивания");
    }
  };

  const renderResultItem = (result) => {
    const pdfFileId = result.pdf_report_id;
    const xlsxFileId = result.xlsx_report_id;
    const isReady = pdfFileId || xlsxFileId;

    return (
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-text-color font-medium">Результат {result.id}</div>
          <div className="text-sm text-text-color/70">Создан: {new Date(result.created_at).toLocaleString()}</div>
        </div>

        <div className="flex items-end gap-2">
          <>
            <FilledButton onClick={() => handleDownloadReport(pdfFileId)}>
              Скачать PDF
            </FilledButton>
            <UnfilledButton onClick={() => handleDownloadReport(xlsxFileId)}>
              Скачать Excel
            </UnfilledButton>
          </>
        </div>
      </div>
    );
  };

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
        <Link
          to={`/app/projects/${projectId}`}
          className="hover:underline"
          onClick={() => workspace && switchWorkspace(workspace.id)}
        >
          <h1>{project?.name}</h1>
        </Link>
        <h1>/</h1>
        <h1 className="text-primary-color">Результаты</h1>
      </nav>

      {!hasAnyResults ? (
        <div className="flex flex-col items-center justify-center py-20 gap-5">
          <p>У вас ещё нет готовых задач.</p>
        </div>
      ) : (
        <>
          <h2 className="text-text-color">Результаты задач план/факт</h2>
          {planFactResults.length ? (
            <Accordion
              items={planFactResults}
              renderHeader={(result) => (
                <div className="flex items-center justify-between gap-3 w-full">
                  <div>
                    <div className="font-semibold text-text-color">Результат {result.id}</div>
                    <div className="text-xs text-text-color/50">Создан: {new Date(result.created_at).toLocaleString()}</div>
                  </div>
                </div>
              )}
              renderContent={(result) => renderResultItem(result)}
            />
          ) : (
            <div className="text-text-color/50">
              Задач типа план/факт ещё не было.
            </div>
          )}

          <h2 className="text-text-color">Результаты фиксации работ</h2>
          {workFixationResults.length ? (
            <Accordion
              items={workFixationResults}
              renderHeader={(result) => (
                <div className="flex items-center justify-between gap-3 w-full">
                  <div>
                    <div className="font-semibold text-text-color">Результат {result.id}</div>
                    <div className="text-xs text-text-color/50">Создан: {new Date(result.created_at).toLocaleString()}</div>
                  </div>
                </div>
              )}
              renderContent={(result) => renderResultItem(result)}
            />
          ) : (
            <div className="text-text-color/50">
              Задач фиксации работ ещё не было.
            </div>
          )}
        </>
      )}
    </>
  )
}
export default ResultPage;