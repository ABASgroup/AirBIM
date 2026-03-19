// Header исключительно для лендинга

import { Link, useLocation } from "react-router-dom";
import { Logo } from "../../components/Logo";
import { FilledButton } from "../../components/FilledButton";
import { UnfilledButton } from "../../components/UnfilledButton";

export const LandingHeader = () => {

  const token = localStorage.getItem("access_token");

  return (
    <header className="h-15 flex items-center justify-between sticky top-0 z-50 px-5 
    bg-surface/70 backdrop-blur-md border-text-color/10 border-b-3">

      <Link to="/">
        <Logo />
      </Link>
      <div>
        {token ? (
          <Link to="/app/dashboard">
            <UnfilledButton color="purple">Личный кабинет</UnfilledButton>
          </Link>
        ) : (
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
        )}
      </div>

    </header>
  );
};