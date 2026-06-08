import { useEffect, useState, useRef } from "react";
import { ActionMenu, Accordion, LoadingSpinner, FilledButton, UnfilledButton } from "@ui";
import { getProjectStages, deleteStage, compareStage } from "@/api/stage";
import { checkStagesProgress } from "@/api/project";
import { ProgressModal } from "@app/components";
import { useToast } from "@/context";

const formatDate = (value) => new Date(value).toLocaleString();

export const StagesAccordion = ({ projectId }) => {
  const [stages, setStages] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeMenuId, setActiveMenuId] = useState(null);
  const menuButtonRefs = useRef({});
  const { showToast } = useToast();

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

  const handleCompare = async (stageId) => {
    try {
      const res = await compareStage(stageId);
      const taskId = res?.data?.id ?? null;
      showToast({
        type: "success",
        title: "Сравнение план/факт",
        message: taskId ? `Задача сравнения запущена: ${taskId}` : "Задача сравнения запущена",
      });
    } catch (error) {
      showToast({
        type: "warning",
        title: "Ошибка",
        message: "Не удалось запустить задачу сравнения план/факт",
      });
    }
  };

  const [showProgressModal, setShowProgressModal] = useState(false);
  const [selectedStageForProgress, setSelectedStageForProgress] = useState(null);

  const openProgressModal = (stageId) => {
    setSelectedStageForProgress(stageId);
    setShowProgressModal(true);
  };

  const handleStartProgress = async (stage1, stage2) => {
    try {
      const res = await checkStagesProgress(projectId, stage1, stage2);
      const taskId = res?.data?.id ?? null;
      setShowProgressModal(false);
      showToast({ type: "success", title: "Задача фиксации прогресса запущена", message: taskId ? `Задача запущена: ${taskId}` : "Задача запущена" });
    } catch (error) {
      showToast({ type: "warning", title: "Ошибка", message: "Не удалось запустить задачу фиксации прогресса" });
    }
  };

  

  if (isLoading) {
    return <LoadingSpinner variant="inline" message="Загрузка этапов..." />;
  }

  if (!stages.length) {
    return <div className="text-text-color/50">Этапы ещё не добавлены</div>;
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
                {stage.name ? stage.name : `Этап ${stage.id}`}
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
          <div>
            <div className="flex items-center justify-between gap-3">
              <div>
                {stage.description ? (
                  <span className="text-text-color">{stage.description}</span>
                ) : (
                  <span className="text-mute-text-color">Описание отсутствует</span>
                )}
                <div className="mt-2 text-xs text-text-color/50">Обновлён: {formatDate(stage.updated_at)}</div>
              </div>

              <div className="flex gap-2">
                <FilledButton onClick={() => handleCompare(stage.id)}>
                  Сравнить план/факт
                </FilledButton>
                <UnfilledButton onClick={() => openProgressModal(stage.id)}>
                  Зафиксировать прогресс
                </UnfilledButton>
              </div>
            </div>
          </div>
        )}
      />
      {showProgressModal && (
        <ProgressModal
          isOpen={showProgressModal}
          onClose={() => setShowProgressModal(false)}
          stages={stages}
          initialStageId={selectedStageForProgress}
          onStart={handleStartProgress}
        />
      )}
      
    </>
  );
};