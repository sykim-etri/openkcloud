import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowPathIcon } from "@heroicons/react/24/solid";
import { fetchWithAuth } from "@/utils/auth";

export default function HardwareSelection() {
  const navigate = useNavigate();
  
  const options = {
    cpu: ["1", "2", "3", "4", "6", "8", "16", "24", "32"],
    memory: ["4", "8", "16", "32", "64", "96", "128"],
    gpu: ["None", "2g.20gb", "3g.40gb", "4g.40gb", "A100 80GB", "A100 80GB × 2"],
  };

  const labels = {
    cpu: "CPU(Core)",
    memory: "Memory(Gi)",
    gpu: "GPU",
  };

  const [selectedValues, setSelectedValues] = useState({ cpu: null, memory: null, gpu: null });
  const [serverName, setServerName] = useState("");
  const [description, setDescription] = useState("");
  const [isServerNameValid, setIsServerNameValid] = useState(true);
  const [isRotating, setIsRotating] = useState(false);
  const [useNewPVC, setUseNewPVC] = useState(true);
  const [existingPVC, setExistingPVC] = useState("");
  const [nodeResources, setNodeResources] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pvcList, setPvcList] = useState([]);

  const validateServerName = (value) => /^[a-zA-Z0-9-]+$/.test(value);
  const handleServerNameChange = (e) => {
    const value = e.target.value;
    setServerName(value);
    setIsServerNameValid(validateServerName(value));
  };

  const handleSelection = (category, value) => {
    setSelectedValues((prev) => ({ ...prev, [category]: value }));
  };

  const fetchNodeResources = async () => {
    try {
      const res = await fetchWithAuth("/metrics/node-resource");
      const data = await res.json();
      setNodeResources(data.nodes || []);
    } catch (err) {
      console.error("Failed to fetch node resources", err);
    }
  };

  const fetchPVCList = async () => {
    try {
      const res = await fetchWithAuth("/server/my-pvcs");
      const data = await res.json();
      setPvcList(data.pvcs || []);
    } catch (err) {
      console.error("Failed to fetch PVC list", err);
    }
  };

  const resetSelection = () => {
    setIsRotating(true);
    setSelectedValues({ cpu: null, memory: null, gpu: null });
    setServerName("");
    setDescription("");

    fetchNodeResources(); // ✅ Re-fetch node resources on reset
    fetchPVCList(); // ✅ Re-fetch PVC list on reset

    setTimeout(() => setIsRotating(false), 500);
  };

  useEffect(() => {
    fetchNodeResources(); // ✅ Call once on initial render
    fetchPVCList(); // ✅ Fetch PVC list on initial render
  }, []);

  const handleCreateServer = async () => {
    //Find selected PVC information
    const selectedPvcInfo = pvcList.find(pvc => pvc.pvc_name === existingPVC);
    
    const payload = {
      image: "<REGISTRY_ADDRESS>/<PROJECT_NAME>/<IMAGE_NAME>",
      cpu: selectedValues.cpu,
      memory: selectedValues.memory,
      gpu: selectedValues.gpu,
      name: serverName,
      description,
      pvc: useNewPVC,
      pvc_id: useNewPVC ? null : selectedPvcInfo?.id,
      pvc_name: useNewPVC ? null : existingPVC,
    };
  
    setIsLoading(true); // ✅ Set loading to true at start
  
    try {
      const response = await fetchWithAuth("/server/create-pod", {
        method: "POST",
        body: JSON.stringify(payload),
      });
  
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Server creation failed");
      }
  
      const result = await response.json();
      alert("✅ GPU server created successfully!");
      console.log(result);
      
      // My Server 탭으로 이동
      navigate("/admin/server");
    } catch (error) {
      console.error("Error creating server:", error);
      alert("❌ An error occurred while creating the server.");
    } finally {
      setIsLoading(false); // ✅ Set loading to false after completion
    }
  };

  // useEffect(() => {
  //   const fetchNodeResources = async () => {
  //     try {
  //       const res = await fetchWithAuth("/metrics/node_resource");
  //       const data = await res.json();
  //       setNodeResources(data);
  //     } catch (err) {
  //       console.error("Failed to fetch node resources", err);
  //     }
  //   };
  //   fetchNodeResources();
  // }, []);

  const allSelected = Object.values(selectedValues).every((value) => value !== null);

  return (
    <div className="relative flex flex-col items-center p-6 space-y-4 w-full">
      <h6 className="mb-2 text-slate-800 text-xl font-semibold">GPU server creation</h6>

      <button
        onClick={resetSelection}
        className="absolute top-0 left-4 p-2 bg-white hover:bg-blue-600 rounded-xl transition duration-200 flex items-center justify-center"
      >
        <ArrowPathIcon
          className={`w-6 h-6 text-black hover:text-white transition-transform duration-500 ${
            isRotating ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Node resource cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full mb-6">
        {nodeResources.map((node) => (
          <div key={node.node} className="bg-white border rounded-xl shadow p-4">
            <h3 className="text-lg font-semibold text-slate-800 mb-2">{node.node}</h3>
            <div className="space-y-1 text-sm text-slate-700">
              <div>CPU: {node.cpu_used} / {node.cpu_total} Core (Remaining: {node.cpu_remaining})</div>
              <div>Memory: {node.memory_used} / {node.memory_total} GB (Remaining: {node.memory_remaining} GB)</div>
              {node.gpu && node.gpu.length > 0 && (
                <div className="mt-2">
                  <div className="font-medium text-slate-800 mb-1">GPU:</div>
                  {node.gpu.map((gpuItem, index) => {
                    const gpuName = Object.keys(gpuItem)[0];
                    const gpuStats = gpuItem[gpuName];
                    return (
                      <div key={index} className="ml-2 text-xs">
                        {/* <span className="font-medium">{gpuName}:</span> {gpuStats.in_use} / {gpuStats.total} (Free: {gpuStats.free}) */}
                        <span className="font-medium">{gpuName}:</span> &nbsp;&nbsp;<strong>{gpuStats.free} / {gpuStats.total}</strong>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Options by category */}
      {Object.keys(options).map((category, index) => {
        const isVisible =
          index === 0 || selectedValues[Object.keys(options)[index - 1]] !== null;

        return (
          <motion.div
            key={category}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: isVisible ? 1 : 0, height: isVisible ? "auto" : 0 }}
            transition={{ duration: 0.5 }}
            className={`overflow-hidden w-full ${isVisible ? "block" : "hidden"}`}
          >
            <div className="flex items-center space-x-6 w-full justify-start mt-2">
              <span className="font-semibold mb-2 text-lg w-20">{labels[category]}</span>

              <div className="flex space-x-6 flex-wrap">
                {options[category].map((option) => (
                  <label key={option} className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="radio"
                      name={category}
                      value={option}
                      checked={selectedValues[category] === option}
                      onChange={() => handleSelection(category, option)}
                      className="hidden"
                    />
                    <div
                      className={`w-5 h-5 border-2 mb-2 rounded-full flex items-center justify-center ${
                        selectedValues[category] === option
                          ? "border-blue-500"
                          : "border-gray-400"
                      }`}
                    >
                      {selectedValues[category] === option && (
                        <div className="w-3 h-3 bg-blue-500 rounded-full" />
                      )}
                    </div>
                    <span className="text-lg mb-2">{option}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Divider */}
            {selectedValues[category] && index < Object.keys(options).length && (
              <motion.div
                initial={{ opacity: 0, width: "0%" }}
                animate={{ opacity: 1, width: "100%" }}
                transition={{ duration: 0.5 }}
                className="border-t border-gray-300 mt-2"
              />
            )}
          </motion.div>
        );
      })}
      <div className="w-full flex flex-col items-start space-y-6">
        {/* Show Server Name + Description together */}
        {allSelected && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="w-full space-y-6 mb-10"
          >
            {/* PVC selection area */}
            <div className="flex items-center space-x-4 mt-2">
              <input
                type="checkbox"
                checked={useNewPVC}
                onChange={(e) => setUseNewPVC(e.target.checked)}
                id="newPVC"
                className="w-4 h-4"
              />
              <label htmlFor="newPVC" className="text-sm text-gray-700 font-medium">
              Create new PVC
              </label>
            </div>
            {/* Existing PVC selection dropdown */}
            <AnimatePresence>
              {!useNewPVC && (
                <motion.div
                  key="pvc-dropdown"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                  className="mt-2 w-full overflow-hidden"
                >
                  <div className="flex items-center space-x-6">
                    <div className="font-semibold text-lg w-40">PVC</div>

                    <select
                      value={existingPVC}
                      onChange={(e) => setExistingPVC(e.target.value)}
                      className="text-center border border-gray-300 rounded-lg px-4 py-2 w-[400px] focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">------------ Select ------------</option>
                      {pvcList.map((pvc) => (
                        <option key={pvc.id} value={pvc.pvc_name}>
                          {pvc.pvc_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* ✅ Divider */}
                  <motion.div
                    initial={{ opacity: 0, width: "0%" }}
                    animate={{ opacity: 1, width: "100%" }}
                    transition={{ duration: 0.5 }}
                    className="border-t border-gray-300 mt-6"
                  />
                </motion.div>
              )}
            </AnimatePresence>
            {/* Server Name */}
            <div className="flex flex-col items-start w-full justify-start space-y-1">
              <div className="flex items-center space-x-6 w-full">
                <span className="font-semibold text-lg w-40">Server Name</span>
                <input
                  type="text"
                  value={serverName}
                  onChange={handleServerNameChange}
                  placeholder="Enter server name"
                  className={`border ${
                    isServerNameValid ? "border-gray-300" : "border-red-500"
                  } rounded-lg px-4 py-2 w-96 focus:outline-none ${
                    isServerNameValid ? "focus:ring-blue-500" : "focus:ring-red-500"
                  } focus:ring-2 transition`}
                />
                {!isServerNameValid && (
                <div className="text-red-500 text-sm ml-40 -mt-1">
                  Only alphabets, numbers, and hyphens (-) are allowed.
                </div>
              )}
              </div>
              
            </div>

            {/* Description */}
            <div className="flex items-start space-x-6 w-full justify-start">
              <span className="font-semibold text-lg w-40 pt-2">Description</span>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter description (Optional)"
                className="border border-gray-300 rounded-lg px-4 py-2 w-[600px] h-[100px] resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
              />
            </div>
            

            
          </motion.div>
        )}
      </div>
      

      {/* Server creation button */}
      {allSelected && serverName && (
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
          className={`mt-4 px-6 py-2 font-semibold rounded-lg shadow-md transition duration-200 flex items-center justify-center ${
            isLoading ? "bg-blue-400 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-600 text-white"
          }`}
          onClick={handleCreateServer}
          disabled={isLoading}
        >
          {isLoading ? (
            <svg className="w-5 h-5 text-white animate-spin" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
          ) : (
            "Create GPU server"
          )}
        </motion.button>
      )}
    </div>
  );
}