// Обертка всего приложения (App)
import { Outlet, useLocation } from "react-router-dom";
import { AppHeader, AppSidebar } from "@app/layout";
import { WorkspaceProvider, TaskProgressProvider } from "@/context";

export const AppLayout = () => {
  const location = useLocation();
  const hideSidebarPaths = ["/app/settings", "/app/workspace"];
  const isSidebarVisible = !hideSidebarPaths.some(path => location.pathname.startsWith(path));

  return (
    <WorkspaceProvider>
      <TaskProgressProvider>
        <div className="flex h-screen">
          {isSidebarVisible && <AppSidebar />}
          <div className="grow flex flex-col">
            <AppHeader />
            <main className="grow pr-10 pl-10 overflow-y-auto">
              <Outlet />
            </main>
          </div>
        </div>
      </TaskProgressProvider>
    </WorkspaceProvider>
  );
}