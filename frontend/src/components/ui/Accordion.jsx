// Скрывающийся компонент-аккордион
import { useState } from "react";

export const Accordion = ({
  items,
  renderHeader,
  renderContent,
  allowMultiple = false,
  className = "",
}) => {
  const [openItems, setOpenItems] = useState([]);

  const toggleItem = (id) => {
    setOpenItems((current) => {
      if (current.includes(id)) {
        return current.filter((item) => item !== id);
      }

      return allowMultiple ? [...current, id] : [id];
    });
  };

  return (
    <div className={`space-y-3 ${className}`}>
      {items.map((item) => {
        const isOpen = openItems.includes(item.id);

        return (
          <div
            key={item.id}
            className="bg-surface rounded-[10px] shadow-bottom overflow-hidden"
          >
            <button
              type="button"
              className="w-full flex items-center justify-between gap-3 px-5 py-4 text-left"
              onClick={() => toggleItem(item.id)}
            >
              {renderHeader(item, { isOpen })}
              <i className={`text-text-color fa-solid fa-chevron-down transition-all
                active:scale-95 cursor-pointer hover:brightness-75 ${isOpen ? "rotate-180" : ""}`}/>
            </button>

            {isOpen && (
              <div className="bg-background-color border border-surface px-5 py-4">
                {renderContent(item)}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};