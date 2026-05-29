// Обертка всего приложения (App)
import { Outlet, useLocation } from "react-router-dom";
import { AppHeader, AppSidebar } from "@app/layout";
import { WorkspaceProvider } from "@/context/WorkspaceContext.jsx";

export const AppLayout = () => {
  const location = useLocation();
  const hideSidebarPaths = ["/app/settings", "/app/workspace"];
  const isSidebarVisible = !hideSidebarPaths.some(path => location.pathname.startsWith(path));

  return (
    <WorkspaceProvider>
      <div className="flex min-h-screen">
        {isSidebarVisible && <AppSidebar />}
        <div className="grow">
          <AppHeader />
          <main className="grow pr-10 pl-10">
            <Outlet />
          </main>
        </div>
      </div>
    </WorkspaceProvider>

  );
}