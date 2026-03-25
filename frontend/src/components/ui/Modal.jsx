// Общий компонент модальных окон 

export const Modal = ({children, title, showBackdrop}) => {
  return (
    <div className="fixed inset-0 z-100 flex items-center justify-center p-5 pointer-events-none">
      {showBackdrop && <div className="absolute inset-0 bg-black/30" />}
      <div className="relative min-w-xl bg-surface backdrop-blur-xl rounded-[5px] 
      border-primary-color border-2 p-10 shadow-xl pointer-events-auto
      [&_p]:text-lg [&_p]:m-2">
        {title && <h2 className="text-3xl font-bold text-text-color mb-5 text-center">{title}</h2>}
        <div className="flex flex-col gap-2">{children}</div>
      </div>
    </div>
  );
};