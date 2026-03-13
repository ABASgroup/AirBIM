// Header для приложения

import { Link, useLocation } from "react-router-dom";
import { Logo } from "../components/Logo";

export const AppHeader = () => {
  return (
    <header className="h-15 flex items-center justify-between sticky top-0 z-50 px-5 
    bg-light-dark/70 backdrop-blur-md border-main-white/10 border-b-3">

      <Logo />

      <div className="flex items-center gap-5">
          <Link to="/app/settings">
            <i className="fa-solid fa-circle-user text-3xl"></i>
          </Link>
      </div>
    </header>
  );
};