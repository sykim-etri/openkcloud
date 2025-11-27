import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, Typography, IconButton, Button } from "@material-tailwind/react";
import { ChevronDownIcon, ChevronUpIcon } from "@heroicons/react/24/solid";
import { fetchWithAuth } from "@/utils/auth";

function toCamelCaseFromEmail(email) {
  if (!email) return "";
  const [first, last] = email.split("@")[0].split(".");
  if (!first || !last) return email;  // fallback
  return first + capitalizeFirstLetter(last);
}

function capitalizeFirstLetter(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function MyServerCard({ server, index, onDelete }) {
  const [expanded, setExpanded] = useState(false);
  const navigate = useNavigate();


  if (!server || index === undefined) {
    return (
      <Card
        className="p-4 border-2 border-dashed border-blue-300 rounded-xl bg-white w-full flex items-center justify-center cursor-pointer hover:bg-blue-50"
        onClick={() => navigate("/admin/create")} // Connect function if needed
      >
        <Typography variant="h5" className="text-blue-400 text-lg font-semibold">
          + Create New Server
        </Typography>
      </Card>
    );
  }

  const {
    userName,
    serverName,
    podName,
    description,
    createdAt,
    cpu,
    memory,
    gpu
  } = server;
  console.log(server)

  const handleDelete = async () => {
    const confirmed = window.confirm("Are you sure you want to delete this server?");
    if (!confirmed) return;

    try {
      const res = await fetchWithAuth(`/server/delete-server`, { 
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name: podName}),
       });
      console.log(podName)
      if (res.ok) {
        alert("Server has been deleted.");
        onDelete?.(server.id); // ✅ Notify parent after deletion
      } else {
        alert("Failed to delete server.");
      }
    } catch (err) {
      console.error("Delete error:", err);
      alert("An error occurred during deletion");
    }
  };

  return (
    <Card className="p-4 shadow-lg border-2 border-blue-gray-900 rounded-xl bg-white w-full ">
      {/* Top area */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <IconButton
            variant="text"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="text-gray-400 hover:bg-blue-gray-50 mr-4 ml-4"
            ripple={false}
          >
            {expanded ? (
              <ChevronUpIcon className="h-5 w-5" />
            ) : (
              <ChevronDownIcon className="h-5 w-5" />
            )}
          </IconButton>

          <Typography
            variant="h6"
            className="text-lg font-semibold text-slate-900 text-blue-gray-300"
          >
            {expanded ? serverName : `Server ${index + 1}(${serverName})`}
          </Typography>
        </div>

        <div className="flex items-center space-x-2 mr-4">
          <Button
            variant="outlined"
            color="red"
            size="md"
            className="hover:bg-red-500 hover:text-white transition-colors"
            onClick={handleDelete}
          >
            Delete
          </Button>
          <Button
            variant="outlined"
            color="blue"
            size="md"
            className="hover:bg-blue-500 hover:text-white transition-colors"
            onClick={() => {
              const _userName = toCamelCaseFromEmail(server.userName); // "yb.jo" → "ybJo"
              // window.open(`/server/${userName}/${server.instance_id}/lab`, "_blank");
              window.open(`/proxy/${_userName}/${server.id}/`, "_blank");
            }}
          >
            Open Server
          </Button>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 ml-10">
          <div className="flex mb-1">
            <div className="w-24 font-semibold text-left text-slate-800">Create at</div>
            <div className="ml-4 text-slate-700">{new Date(createdAt).toLocaleString()}</div>
          </div>
          <div className="flex mb-1">
            <div className="w-24 font-semibold text-left text-slate-800">Name</div>
            <div className="ml-4 text-slate-700">{serverName}</div>
          </div>
          <div className="flex mb-6">
            <div className="w-24 font-semibold text-left text-slate-800">Description</div>
            <div className="ml-4 text-slate-700">{description}</div>
          </div>
          
          <div className="flex mb-1">
            <div className="w-24 font-semibold text-left text-slate-800">CPU</div>
            <div className="ml-4 text-slate-700">{cpu}</div>
          </div>
          <div className="flex mb-1">
            <div className="w-24 font-semibold text-left text-slate-800">Memory</div>
            <div className="ml-4 text-slate-700">{memory}</div>
          </div>
          <div className="flex mb-1">
            <div className="w-24 font-semibold text-left text-slate-800">GPU</div>
            <div className="ml-4 text-slate-700">{gpu}</div>
          </div>

          {/* Grafana graph area */}
          <div className="mt-4 border-t border-blue-gray-200 pt-4">
            <div className="w-full h-32 flex items-center justify-center bg-blue-gray-50 text-blue-gray-600 rounded">
              Connect Grafana Graph
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
