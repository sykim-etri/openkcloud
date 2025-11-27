import React from 'react';
import { Button } from "@material-tailwind/react";

function UserDashboard() {
  const user = JSON.parse(localStorage.getItem('user'));

  const handleLogout = () => {
    localStorage.removeItem('user');
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white shadow-md rounded-lg p-6">
        <h1 className="text-3xl font-bold mb-4">User Dashboard</h1>
        <div className="mb-4">
          <p>Welcome, <strong>{user.name}</strong>!</p>
          <p>Department: {user.department}</p>
          <p>Role: {user.role}</p>
        </div>
        <Button onClick={handleLogout} color="red">
          Logout
        </Button>
      </div>
    </div>
  );
}

export default UserDashboard;