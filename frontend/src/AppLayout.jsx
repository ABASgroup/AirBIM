import { Outlet, useLocation } from "react-router-dom";
import { AppHeader } from "../src/components/AppHeader.jsx"
import { AppSidebar } from "./components/AppSidebar.jsx";

const AppLayout = () => {

  const location = useLocation();
  const hideSidebarPaths = ["/app/settings"];
  const isSidebarVisible = !hideSidebarPaths.includes(location.pathname);

  return (
    <div className="flex min-h-screen">
      {isSidebarVisible && <AppSidebar />}
      <div className="grow">
        <AppHeader />
        <main className="grow pr-10 pl-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
export default AppLayout;