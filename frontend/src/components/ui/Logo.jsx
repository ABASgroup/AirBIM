// Логотип AirBIM с изображением и названием
import logoImage from "@/assets/images/logo.png";

export const Logo = () => {
  return (
    <div className="h-full shrink-0 flex items-center gap-2 py-2">
      <img
        src={logoImage}
        alt="Logo"
        className="h-full w-auto object-contain"
      />
    </div>
  );
};