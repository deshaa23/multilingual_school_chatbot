import { Routes, Route } from "react-router-dom";

import Login from "../pages/Login";
import Register from "../pages/Register";
import Dashboard from "../pages/Dashboard";
import NotFound from "../pages/NotFound";
import ParentRegister from "../pages/ParentRegister";
import ProtectedRoute from "../components/auth/ProtectedRoute";

function AppRoutes() {
  return (
    <Routes>

<Route path="/" element={<Login />} />

<Route path="/register" element={<Register />} />

<Route
    path="/parent-register"
    element={<ParentRegister />}
/>

<Route
    path="/dashboard"
    element={
        <ProtectedRoute>
            <Dashboard />
        </ProtectedRoute>
    }
/>

<Route
    path="*"
    element={<NotFound />}
/>

</Routes>
  );
}

export default AppRoutes;