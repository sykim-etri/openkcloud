// src/components/ProtectedRoute.jsx
import React from "react";
import { Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode"; // Changed import statement

const isTokenValid = (token) => {
  try {
    const decoded = jwtDecode(token); // Remove .default
    // If it's a dummy token and has no exp, treat as valid
    if (!decoded.exp) return true;
    return decoded.exp * 1000 > Date.now(); // exp is in seconds, Date.now() is in milliseconds
  } catch (err) {
    console.error("JWT decode error:", err);
    return false;
  }
};

const ProtectedRoute = ({ children, requiredRole }) => {
  const token = localStorage.getItem("access_token");
  let user = null;
  
  try {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      user = JSON.parse(userStr);
    }
  } catch (err) {
    console.error("Error parsing user:", err);
    return <Navigate to="/" replace />;
  }

  if (!token || !user || !isTokenValid(token)) {
    // console.log("Authentication failed - redirecting to login");
    return <Navigate to="/" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    // console.log(`Role mismatch - required: ${requiredRole}, user has: ${user.role}`);
    return <Navigate to={`/${user.role}`} replace />;
  }

//   console.log("Authentication successful");
  return children;
};

export default ProtectedRoute;