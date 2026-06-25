// Routing for the app
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { AppLayout, ExternalLayout } from "@app/layout"
import { WorkspaceProvider } from "@/context";
import {
  LandingPage, LoginPage, RegistrationPage, DashboardPage, SettingsPage,
  WorkspacePage, ProjectPage, InvitePage, PotreeScenePage, ResultPage
} from "@/pages"

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem("access_token");
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const PublicRoute = ({ children }) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    return <Navigate to="/app/dashboard" replace />;
  }
  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />

        <Route element={<ExternalLayout />}>
          <Route path="invites/:token" element={<InvitePage />} />

          <Route path="/login" element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          } />

          <Route path="/register" element={
            <PublicRoute>
              <RegistrationPage />
            </PublicRoute>
          } />
        </Route>

        <Route path="/login" element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>} />

        <Route path="/register" element={
          <PublicRoute>
            <RegistrationPage />
          </PublicRoute>} />

        <Route path="invites/:token" element={
          <ProtectedRoute>
            <InvitePage />
          </ProtectedRoute>} />

        <Route path="/app/projects/:projectId/scene"
          element={
            <ProtectedRoute>
              <WorkspaceProvider>
                <PotreeScenePage />
              </WorkspaceProvider>
            </ProtectedRoute>
          }
        />

        <Route path="/app" element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }>
          <Route path="settings" element={<SettingsPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="workspace/:workspaceId" element={<WorkspacePage />} />
          <Route path="projects/:projectId" element={<ProjectPage />} />
          <Route path="projects/:projectId/results" element={<ResultPage />} />
          <Route index element={<Navigate to="dashboard" replace />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
