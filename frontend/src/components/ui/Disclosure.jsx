// Скрываемый блок контента на странице
export const Disclosure = ({ title, isOpen, onToggle, children }) => {
  return (
    <div className={`w-full`}>
      <div 
        onClick={() => onToggle(!isOpen)}
        className="cursor-pointer group py-3"
      >
        <div className="flex items-center gap-4">
          {/* Текст заголовка */}
          <span className="text-mute-text-color group-hover:text-text-color transition-colors uppercase text-xs font-bold tracking-widest whitespace-nowrap">
            {title}
          </span>
          
          {/* Та самая hr-полоса, которая тянется */}
          <div className="grow border-t border-border-color/50 group-hover:border-text-color/20 transition-colors"></div>
          
          {/* Иконка стрелочки */}
          <i className={`fa-solid fa-chevron-down text-mute-text-color group-hover:text-text-color transition-all duration-300 ${isOpen ? "rotate-180" : ""}`}></i>
        </div>
      </div>
      {/* Раскрывающийся контент */}
      {isOpen && (
        <div className="mt-2 pb-4 animate-in fade-in slide-in-from-top-1 duration-200">
          {children}
        </div>
      )}
    </div>
  );
};