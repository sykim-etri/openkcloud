import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import SignInPage from "@/pages/SignInPage";
import AdminDashboard from "@/pages/AdminDashboard";
import ProtectedRoute from "@/components/Secure/ProtectedRouter";

import DashboardStatus from "@/layout/DashboardStatus";
import DashboardPod from "@/layout/CreatePod";
import MyServer from "@/layout/MyServer"
import NfsFileBrowser from "@/layout/StorageManagement"

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SignInPage />} />

        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminDashboard /> {/* This is Layout */}
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="home" />} />
          <Route path="home" element={<DashboardStatus />} />
          <Route path="create" element={<DashboardPod />} />
          <Route path="storage/*" element={<NfsFileBrowser />} />
          <Route path="server/*" element={<MyServer />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;