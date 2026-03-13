// Компонент кнопки с контуром

export const UnfilledButton = ({ children, color = "purple", className = "", ...props }) => {
  const colorMap = {
    purple: "border-main-purple text-main-purple bg-transparent",
    white: "border-main-white text-main-white",
    warning: "border-warning text-warning",
  };

  return (
    <button
      className={`
        min-w-[100px] px-6 py-3
        border-2 rounded-[10px] font-bold
        transition-all active:scale-95
        cursor-pointer
        ${colorMap[color] || colorMap.purple}
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
};