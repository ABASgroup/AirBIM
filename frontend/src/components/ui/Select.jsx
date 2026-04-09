// Выпадающее окно с выбором опции
import { useState, useRef, useEffect } from "react";

export const Select = ({
  value,
  onChange,
  options,
  placeholder,
  className = "",
  bgClassName = "bg-background-color",
  disabled = false }) => {

  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef(null);
  const selectedOption = options.find(o => o.value === value);
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);


  return (
    <div ref={ref} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={`
          w-full h-full rounded-[5px] p-4 py-3 flex items-center justify-between border-none
          ${bgClassName}
          ${disabled ? "cursor-default text-mute-text-color" : "cursor-pointer"}
        `}
      >
        <span className={`${disabled ? "text-mute-text-color" : ""}`}>{selectedOption?.label || placeholder}</span>

        {disabled ? (
          <i className="fa-solid fa-lock text-mute-text-color" />
        ) : (
          <i className={`fa-solid fa-chevron-down text-text-color transition-transform ${isOpen ? "rotate-180" : ""}`} />
        )}
      </button>
      {isOpen && (
        <div className={`absolute top-full left-0 w-full mt-2 ${bgClassName} rounded-[5px] z-50 overflow-hidden`}>
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`
                w-full px-4 py-3 text-left cursor-pointer border-none bg-transparent hover:bg-mute-text-color
                ${option.value === value ? "bg-mute-text-color" : ""}
              `}
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};