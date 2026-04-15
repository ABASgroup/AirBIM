// Общий лайаут для внешних страниц
import { LandingHeader } from "@landing";
import { Outlet } from "react-router-dom";

export const ExternalLayout = () => (
  <>
    <LandingHeader />
    <main className="flex items-center justify-center min-h-[80vh]">
      <Outlet />
    </main>
  </>
);