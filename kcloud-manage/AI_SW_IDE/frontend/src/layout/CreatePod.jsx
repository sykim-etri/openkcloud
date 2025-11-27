// src/components/CustomDashboard.jsx
import React, { useState, useEffect } from 'react';
import { Card } from "@material-tailwind/react";
import Radio from "../components/RadioButton";
import ExpandingRadio from '../components/ExpendingRadioButton';
import GPUNode from '../components/GPUNode';


const DashboardPod = () => {
  const [data, setData] = useState({
    nodeList: ['worker1', 'worker2'], // Initial value (can be changed when API is called)
    gpuData: {
      'worker1': {
        0: [
          { flavor: '2g.20g', compute: 2, user: 'example user', status: 'RUNNING' },
          { flavor: '2g.20g', compute: 2, user: 'example user', status: 'EMPTY' },
          { flavor: '3g.40g', compute: 3, user: 'example user', status: 'RUNNING' },
        ],
        1: [
          { flavor: '2g.20g', compute: 2, user: 'example user', status: 'EMPTY' },
          { flavor: '2g.20g', compute: 2, user: 'example user', status: 'EMPTY' },
          { flavor: '3g.40g', compute: 3, user: 'example user', status: 'RUNNING' },
        ]
      },
      'worker2': {
        0: [
          { flavor: '2g.20g', compute: 0, user: 'example user', status: 'EMPTY' }
        ],
        1: [
          { flavor: '2g.20g', compute: 2, user: 'example user', status: 'RUNNING' },
          { flavor: '2g.20g', compute: 2, user: 'example user', status: 'RUNNING' },
          { flavor: '2g.40g', compute: 2, user: 'example user', status: 'RUNNING' },
          { flavor: '2g.40g', compute: 2, user: 'example user', status: 'RUNNING' },
        ]
      }
    }
  });

  const gridClass = `grid grid-cols-${data.nodeList.length} gap-4 mb-10`;

  return (
    <div className="p-10 ">

      <Card className='max p-6 shadow-xl shadow-blue-gray-900/5 border border-gray-300 rounded-xl bg-white'>
        {/* <Radio></Radio> */}
        <ExpandingRadio></ExpandingRadio>
      </Card>
    
    </div>
  );
};

export default DashboardPod;