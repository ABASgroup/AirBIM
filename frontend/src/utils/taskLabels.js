const TASK_TYPE_LABELS = {
  "converting bim": "Конвертация BIM",
  "converting point cloud": "Конвертация облака точек",
  "comparing plan fact": "Сравнение план/факт",
  "checking progress": "Фиксация прогресса",
};

export const getTaskTypeLabel = (type) => TASK_TYPE_LABELS[type] || type;
