// Header приложения
import { Link, useLocation } from "react-router-dom";
import { Logo, UnfilledButton } from "@ui";

export const AppHeader = () => {
  const location = useLocation();
  const isDashboard = location.pathname === "/app/dashboard";
  return (
    <header className="h-15 flex items-center justify-between sticky top-0 z-50 px-5 
    bg-surface/70 backdrop-blur-md border-border-color border-b-3">
      <div className="flex items-center justify-between gap-5">
        <Logo />
        {!isDashboard && (
          <Link to="/app/dashboard">
            <UnfilledButton>Личный кабинет</UnfilledButton>
          </Link>
        )}
      </div>
      <div className="flex items-center gap-5">
        <Link to="/app/settings">
          <i className="fa-solid fa-circle-user text-3xl"></i>
        </Link>
      </div>
    </header>
  );
};