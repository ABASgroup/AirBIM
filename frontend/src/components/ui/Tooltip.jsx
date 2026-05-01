// Компонент всплывающих подсказок
import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { useFloating, offset, flip, shift, autoUpdate } from "@floating-ui/react-dom";

export const Tooltip = ({ content, children, className = "", disabled = false }) => {
  const [isOpen, setIsOpen] = useState(false);
  const arrowRef = useRef(null);

  const { x, y, strategy, refs, placement, middlewareData } = useFloating({
    open: isOpen,
    onOpenChange: setIsOpen,
    placement: "left",
    whileElementsMounted: autoUpdate,
    middleware: [
      offset(10),
      flip({
        fallbackPlacements: ["right", "top", "bottom"],
      }),
      shift({ padding: 5 })
    ],
  });

  useEffect(() => {
    if (refs.setReference) {
    }
  }, [refs]);

  return (
    <>
      <div
        ref={refs.setReference}
        onMouseEnter={() => !disabled && setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        className={className}
      >
        {children}
      </div>
      {isOpen && !disabled && createPortal(
        <div
          ref={refs.setFloating}
          className="fixed z-50 bg-surface/50 backdrop-blur-md border-2 border-text-color/20 
          rounded-[5px] p-3 max-w-xs shadow-bottom"
          style={{ position: strategy, top: y ?? 0, left: x ?? 0, width: "max-content" }}
        >
          {content}
        </div>,
        document.body
      )}
    </>
  );
};