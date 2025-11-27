// src/utils/auth.js
const API_URL = window.ENV?.API_URL || import.meta.env.VITE_API_URL || '';

export async function fetchWithAuth(url, options = {}) {
  let accessToken = localStorage.getItem("access_token");
  const refreshToken = localStorage.getItem("refresh_token");

  if (!accessToken) {
    console.warn("❌ No access token. Login required");
    alert("Login is required.");
    window.location.href = "/";
    return;
  }

  let response = await fetch(`${API_URL}${url}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
  });


  if (response.status === 401 && refreshToken) {
    const refreshRes = await fetch(`${API_URL}/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (refreshRes.ok) {
      const data = await refreshRes.json();
      accessToken = data.token;
      localStorage.setItem("access_token", accessToken);

      // Retry request
      response = await fetch(`${API_URL}${url}`, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
      });
    } else {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      alert("Session has expired. Please log in again.");
      window.location.href = "/";
      return;
    }
  }

  return response;
}

// Logout function
export function logout() {
  // Remove tokens from localStorage
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  
  // Add any additional cleanup work needed here
  
  // Redirect to login page
  window.location.href = "/";
}

// Check login status
export function isLoggedIn() {
  const accessToken = localStorage.getItem("access_token");
  return !!accessToken;
}

// Get current user information (decode from token)
export function getCurrentUser() {
  const accessToken = localStorage.getItem("access_token");
  
  if (!accessToken) {
    return null;
  }
  
  try {
    // Decode JWT token (simple method)
    const payload = JSON.parse(atob(accessToken.split('.')[1]));
    return {
      username: payload.sub || payload.username || "User",
      role: payload.role || "user",
      exp: payload.exp
    };
  } catch (error) {
    console.error("Token decode failed:", error);
    return {
      username: "User",
      role: "user"
    };
  }
}