import React, { useEffect, useState } from "react";
import { MyServerCard } from '@/components/MyServerCard';
import { fetchWithAuth } from "@/utils/auth";


const MyServer = () => {
  const [servers, setServers] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetchWithAuth("/server/my-server");
        if (!res || !res.ok) {
          throw new Error("Unable to receive response from server.");
        }
        const data = await res.json();
        setServers(data);
      } catch (error) {
        console.error("Failed to load server list:", error);
      }
    };

    fetchData();
  }, []);

  const handleDelete = (id) => {
    setServers((prev) => prev.filter((server) => server.id !== id));
  };

  return (
    <div className="space-y-4">
      {servers.map((server, index) => (
        <MyServerCard key={server.id} server={server} index={index} onDelete={handleDelete} />
      ))}

      {/* 🔽 Additionally render "empty card" */}
      <MyServerCard />
    </div>
  );
}

export default MyServer;