// Header исключительно для лендинга

import { Link, useLocation } from "react-router-dom";
import { Logo } from "../../components/Logo";
import { FilledButton } from "../../components/FilledButton";
import { UnfilledButton } from "../../components/UnfilledButton";

export const LandingHeader = () => {
  return (
    <header className="bg-light-dark/70 backdrop-blur-md h-15 flex items-center justify-between sticky top-0 z-50 px-5">
      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-main-white/10 shadow-[0_1px_10px_rgba(255,255,255,0.05)]"></div>

      <Link to="/">
        <Logo />
      </Link>

      <div className="flex items-center gap-5">
        {location.pathname !== '/login' && (
          <Link to="/login">
            <UnfilledButton color="purple">Войти</UnfilledButton>
          </Link>
        )}

        {location.pathname !== '/register' && (
          <Link to="/register">
            <FilledButton color="purple">Зарегистрироваться</FilledButton>
          </Link>
        )}
      </div>
    </header>
  );
};