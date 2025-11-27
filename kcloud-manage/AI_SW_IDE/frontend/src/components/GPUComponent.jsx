import React from 'react';
import PixelCard from './PixelCard';
import { Card, CardBody, Tooltip } from "@material-tailwind/react";

const WIDTH = {
  0: 370,
  2: 80,
  3: 180,
  4: 180
};

const GPUComponent = ({
  compute=2,
  gpuId=0,
  migId=null,
  flavor='2g.20gb',
  user=null,
  status=null
}) => {
  return (
    <div>
      <Card className="p-2 shadow-none">
        {/* <Tooltip content={<span>GPU ID: {gpuId}<br />Status:{status}<br />Flavor: {flavor}<br />User: {user}</span>} placement="bottom" className="bg-gray-700 text-white p-2 rounded-md shadow-lg"> */}
        <Tooltip 
          content={
            <div className="bg-gray-700 text-white p-2 rounded-md text-sm">
              <div className="grid grid-cols-2 gap-x-2">
                <span className="font-semibold">GPU ID</span> <span >{gpuId}</span>
                {migId !== null && (
                  <>
                    <span className="font-semibold">MIG ID</span> <span>{migId}</span>
                  </>
                )}
                <span className="font-semibold">Status</span> <span>{status}</span>
                <span className="font-semibold">Flavor</span> <span>{flavor}</span>
                <span className="font-semibold">User</span> <span>{user}</span>
              </div>
            </div>
          } 
          placement="bottom" 
          className="bg-gray-700 text-white p-2 rounded-md"
        >
          <Card className='shadow-none border-none'>
            <PixelCard status={status} variant='pink' width={WIDTH[compute]} height={200}/>
          </Card>
        </Tooltip>
      </Card>
    </div>
  );
};

export default GPUComponent;