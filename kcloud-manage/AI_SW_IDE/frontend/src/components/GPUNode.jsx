import React from 'react';
import GPUComponent from './GPUComponent';

const GPUNode = ({ gpuId, data }) => {
  return (
    // Changed to flex container, applied space-x-2 for spacing between items
    <div className="flex shadow-none">
      {data.map((item, index) => (
        <GPUComponent
          key={index}
          compute={item.compute}
          gpuId={gpuId}
          migId={item.migId}
          flavor={item.flavor}
          user={item.user}
          status={item.status}
        />
      ))}
    </div>
  );
};

export default GPUNode;