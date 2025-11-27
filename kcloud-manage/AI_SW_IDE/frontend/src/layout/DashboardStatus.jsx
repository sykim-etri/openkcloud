// src/components/CustomDashboard.jsx
import React, { useState, useEffect } from 'react';
import RunningPodTable from "../components/RunningPodTable";
import GPUNode from '../components/GPUNode';
import LoadingSpinner from '../components/Loading';
import { fetchWithAuth } from '@/utils/auth';


const DashboardStatus = () => {
  const [data, setData] = useState({
    nodeList: [],
    gpuData: {}
  });
  const [loading, setLoading] = useState(true);

  // Function to fetch data
  const fetchData = async () => {
    try {
      const response = await fetchWithAuth('/metrics/gpu-resource');
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error("Error fetching API data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Call data immediately on component mount
    fetchData();

    // Polling (execute fetchData every 15 seconds)
    const interval = setInterval(() => {
      fetchData();
    }, 15000);

    // Cleanup interval on unmount
    return () => clearInterval(interval);
  }, []);


  if (loading) {
    return <LoadingSpinner />;
  }

  const gridClass = `grid grid-cols-${data.nodeList.length} gap-4 mb-10`;

  return (
    <div className="p-10 ">
      <div className={gridClass} style={{ height: `500px` }}>
        {
          data.nodeList.map((nodeName) => (
            <div key={nodeName} className="p-2 flex flex-col items-center">
              <h1 className="text-2xl font-bold mb-2 text-center">{nodeName}</h1>
              {Object.keys(data.gpuData[nodeName]).map((gpuId) => (
                <GPUNode
                  key={nodeName + "-" + gpuId}
                  gpuId={gpuId}
                  data={data.gpuData[nodeName][gpuId]}
                />
              ))}
            </div>
          ))
        }
      </div>
      <RunningPodTable />
    
    </div>
  );
};

export default DashboardStatus;

