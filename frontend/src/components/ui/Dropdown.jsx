// Общий компонент выпадающего окна
import { useRef, useEffect } from "react";

export const Dropdown = ({ label, children, isOpen, onToggle, className = "" }) => {
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
      <div 
        onClick={() => onToggle(!isOpen)} 
        className={`flex items-center justify-between cursor-pointer border-border-color border-b-3 ${className}`}
      >
        <span>{label}</span>
        <i className={`fa-solid fa-chevron-down transition-transform text-text-color ${isOpen ? "rotate-180" : ""}`}></i>
      </div>
      {isOpen && (
        <div className="absolute top-full left-0 z-60 bg-surface rounded-[5px] max-h-[70vh] overflow-y-auto overflow-x-hidden my-2">
          {children}
        </div>
      )}
    </div>
  );
};