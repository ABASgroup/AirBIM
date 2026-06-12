import { useState } from "react";
import { Modal, FilledButton, UnfilledButton, Input } from "@ui";

export const PlanFactModal = ({ isOpen = true, onClose, stageId, stageName, onStart }) => {
  const [tolerance, setTolerance] = useState(0.05);
  const handleStart = () => {
    onStart(stageId, tolerance);
  };

  return (
    <Modal title="Сравнение план/факт" showBackdrop={true} onClose={onClose}>
      <div className="space-y-4">
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
          <FilledButton onClick={handleStart}>Запустить</FilledButton>
        </div>
      </div>
    </Modal>
  );
};