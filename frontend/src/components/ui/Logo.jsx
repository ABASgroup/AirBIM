// Логотип AirBIM с изображением и названием

import logoImage from "@/assets/images/logo.png";

export const Logo = () => {
  return (
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 shrink-0">
        <img 
          src={logoImage}
          alt="Logo" 
          className="w-full h-full object-contain" 
        />
      </div>

      <div className="flex items-center gap-0">
        <span className="text-text-color text-2xl tracking-tight">Air</span>
        <span className="text-primary-color font-bold text-2xl tracking-tight">BIM</span>
      </div>
    </div>
  );
};