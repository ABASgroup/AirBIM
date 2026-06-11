import { useState } from "react";
import { Modal, FilledButton, UnfilledButton, Select, Input } from "@ui";

export const ProgressModal = ({ isOpen = true, onClose, stages = [], initialStageId = null, onStart }) => {
  const [first, setFirst] = useState(initialStageId);
  const [second, setSecond] = useState(null);
  const [tolerance, setTolerance] = useState(0.05);

  const options = stages.map((s) => ({ value: s.id, label: s.name || `Этап ${s.id}` }));

  const handleStart = () => {
    if (!first || !second) return;
    onStart(first, second, tolerance);
  };

  return (
    <Modal title="Фиксация прогресса" showBackdrop={true} onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label>Первый этап</label>
          <Select
            value={first}
            onChange={setFirst}
            options={options}
            placeholder="Выберите этап"
            disabled={true}
          />
        </div>

        <div>
          <label>Второй этап</label>
          <Select
            value={second}
            onChange={setSecond}
            options={options.filter((o) => o.value !== first)}
            placeholder="Выберите этап для сравнения"
          />
        </div>

        <div>
          <label>Допуск, м</label>
          <Input
            type="number"
            min={0}
            max={100}
            step={0.001}
            value={tolerance}
            onChange={(e) => setTolerance(parseFloat(e.target.value))}
          />
        </div>

        <div className="flex items-center gap-2 justify-end">
          <UnfilledButton onClick={onClose}>Отмена</UnfilledButton>
          <FilledButton onClick={handleStart} disabled={!second}>Запустить</FilledButton>
        </div>
      </div>
    </Modal>
  );
};
