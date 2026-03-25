import { useRef, useEffect } from "react";

export const Dropdown = ({ trigger, children, isOpen, onToggle }) => {
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        onToggle(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, onToggle]);

  return (
    <div className="relative w-full" ref={dropdownRef}>
      <div onClick={() => onToggle(!isOpen)}>{trigger}</div>
      {isOpen && (
        <div className="absolute top-full left-0 z-60 bg-surface rounded-[5px] max-h-[70vh] overflow-y-auto overflow-x-hidden my-2">
          {children}
        </div>
      )}
    </div>
  );
};