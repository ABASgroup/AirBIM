import { useEffect, useState, useRef } from "react";
import { ActionMenu, Accordion, LoadingSpinner } from "@ui";
import { getProjectStages, deleteStage } from "@/api/stage";

const formatDate = (value) => new Date(value).toLocaleString();

export const StagesAccordion = ({ projectId }) => {
  const [stages, setStages] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeMenuId, setActiveMenuId] = useState(null);
  const menuButtonRefs = useRef({});

  const loadStages = async () => {
    setIsLoading(true);
    try {
      const res = await getProjectStages(projectId);
      setStages(res.data || []);
    } catch (error) {
      showToast({
        type: "warning",
        title: "Ошибка",
        message: "Не удалось загрузить этапы",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStages();
  }, [projectId]);

  const handleDelete = async (stageId) => {
    try {
      await deleteStage(stageId);
      setActiveMenuId(null);
      await loadStages();
    } catch (error) {
    }
  };

  if (isLoading) {
    return <LoadingSpinner variant="inline" message="Загрузка этапов..." />;
  }

  if (!stages.length) {
    return <div className="text-text-color">Этапы ещё не добавлены</div>;
  }

  return (
    <>
      <h2 className="font-semibold mb-4 text-text-color">Загруженные этапы</h2>
      <Accordion
        items={stages}
        renderHeader={(stage) => (
          <div className="flex items-center justify-between gap-3 w-full">
            <div>
              <div className="font-semibold text-text-color">
                Этап {stage.id}
              </div>
              <div className="text-xs text-text-color/60">
                Создан: {formatDate(stage.created_at)}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span
                role="button"
                ref={(el) => (menuButtonRefs.current[stage.id] = el)}
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveMenuId(activeMenuId === stage.id ? null : stage.id);
                }}
              >
                <i className="fa-solid fa-bars text-text-color active:scale-95 cursor-pointer hover:brightness-75" />
              </span>

              {activeMenuId === stage.id && (
                <ActionMenu
                  isOpen={true}
                  onClose={() => setActiveMenuId(null)}
                  buttonRef={{ current: menuButtonRefs.current[stage.id] }}
                >
                  <button type="button" onClick={() => handleDelete(stage.id)}>
                    <i className="fa-solid fa-trash"></i>
                    Удалить
                  </button>
                </ActionMenu>
              )}
            </div>
          </div>
        )}
        renderContent={(stage) => (
          <div className="text-sm text-text-color">
            <div>ID: {stage.id}</div>
            <div>Обновлён: {formatDate(stage.updated_at)}</div>
          </div>
        )}
      />
    </>
  );
};