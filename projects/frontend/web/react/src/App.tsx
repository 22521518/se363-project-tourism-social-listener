import { Navigate, Outlet, Route, Routes } from "react-router";
import Dashboard from "./routes/Dashboard";
import PostAnalysis from "./routes/PostAnalysis";
import Geography from "./routes/Geography";

import { Header } from "./components/Header";
import { useState } from "react";
import PostDetail from "./routes/PostDetail";

const MainLayout = () => {
  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
      }}
    >
      <Header />
      <Outlet />
    </div>
  );
};
export default function App() {
  return (
    <Routes>
      {/* redirect root to /dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route element={<MainLayout />}>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="posts" element={<PostAnalysis />} />
        <Route path="posts/:id" element={<PostDetail />} />
        <Route path="geography" element={<Geography />} />
        <Route path="geography/:continentId" element={<Geography />} />
        <Route path="geography/:continentId/:countryId" element={<Geography />} />
      </Route>
    </Routes>
  );
}
