// Компонент всплывающих подсказок
import { useState, useRef } from "react";

export const Tooltip = ({ content, children, className = "", disabled = false }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0, transform: "translate(-50%, -100%)" });
  const triggerRef = useRef(null);

  const handleMouseEnter = () => {
    if (triggerRef.current && !disabled) {
      const rect = triggerRef.current.getBoundingClientRect();

      // TODO: сделать умное отображение в зависимости от положения на экране, либо кастомные варианты
      setPosition({
        top: rect.top + rect.height,
        left: rect.left - 10,
        transform: "translate(-100%, -50%)",
      });
      setIsVisible(true);
    }
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className={className}
      >
        {children}
      </div>
      {isVisible && !disabled && (
        <div
          className="fixed z-50 bg-surface/50 backdrop-blur-md border-2 border-text-color/20 rounded-[5px] p-3 max-w-xs
          shadow-bottom"
          style={{
            top: position.top,
            left: position.left,
            transform: position.transform,
          }}
        >
          {content}
        </div>
      )}
    </>
  );
};