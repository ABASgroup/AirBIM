// Компонента прогрессбара
import { getTaskTypeLabel } from "@/utils/taskLabels";

export const ProgressBar = ({ taskType, entityType, entityId, percentage }) => {
  return (
    <div className="w-full mb-3">
      <div className="flex justify-between items-baseline mb-1 gap-2 text-text-color">
        <div className="min-w-0 flex-1">
          <div className="truncate text-xs font-medium mb-0.5">{getTaskTypeLabel(taskType)}</div>
          <div className="truncate text-text-color/50 text-[10px] mb-0.5">
           {entityId}
          </div>
        </div>
        <span className="shrink-0 text-xs font-bold text-text-color">{percentage}%</span>
      </div>
      <div className="h-3 w-full bg-background-color rounded-full overflow-hidden">
        <div
          className="h-full bg-primary-color transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
