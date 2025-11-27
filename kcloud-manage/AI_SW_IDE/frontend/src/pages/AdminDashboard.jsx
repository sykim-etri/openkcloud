// // AdminDashboard.jsx
// import { Routes, Route, Outlet, Navigate } from "react-router-dom";
// import Sidebar from "../layout/Sidebar";
// import { StickyNavbar } from "@/components/Navbar";
// import { ThemeProvider } from "@material-tailwind/react";

// import DashboardStatus from "@/layout/DashboardStatus";
// import DashboardPod from "@/layout/CreatePod";
// import MyServer from "@/layout/MyServer"
// import NfsFileBrowser from "@/layout/StorageManagement"
// // import Tables from "../components/Tables";
// // import Notifications from "../components/Notifications";

// const AdminDashboard = () => {
//   return (
//     <ThemeProvider>
//       <div className="flex h-screen">
//         <div className="w-[256px] flex-shrink-0">
//           <Sidebar />
//         </div>
//         <div className="flex flex-col flex-1 overflow-hidden">
//           <StickyNavbar />
//           <main className="p-6 overflow-auto">
//             {/* 여기에 Admin 내부 라우팅을 구성 */}
//             <Routes>
//               <Route path="/" element={<Navigate to="home" />} />
//               <Route path="home" element={<DashboardStatus />} />
//               <Route path="create" element={<DashboardPod />} />
//               <Route path="storage/*" element={<NfsFileBrowser />} />
//               <Route path="server/*" element={<MyServer />} />
//               <Route path="*" element={<Navigate to="/admin" />} />
//             </Routes>
//           </main>
//         </div>
//       </div>
//     </ThemeProvider>
//   );
// };

// export default AdminDashboard;


import { Outlet } from "react-router-dom";
import Sidebar from "../layout/Sidebar";
import { StickyNavbar } from "@/components/Navbar";
import { ThemeProvider } from "@material-tailwind/react";

const AdminDashboard = () => {
  return (
    <ThemeProvider>
      <div className="flex h-screen">
        <div className="w-[256px] flex-shrink-0">
          <Sidebar />
        </div>
        <div className="flex flex-col flex-1 overflow-hidden">
          <StickyNavbar />
          <main className="p-6 overflow-auto">
            <Outlet /> {/* Internal pages are rendered here */}
          </main>
        </div>
      </div>
    </ThemeProvider>
  );
};

export default AdminDashboard;