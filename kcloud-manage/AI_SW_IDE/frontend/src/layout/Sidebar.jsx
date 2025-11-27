import React from "react";
import {
  HomeIcon,
  CubeIcon,
  CubeTransparentIcon,
  FolderIcon,
  RectangleGroupIcon
} from "@heroicons/react/24/solid";
import { NavLink } from "react-router-dom";
import { Typography } from "@material-tailwind/react";

const Sidebar = () => {
  const routes = [
    {
      title: "Main",
      pages: [
        {
          icon: <HomeIcon className="h-5 w-5" />,
          name: "Home",
          path: "/admin/home",  // ✅ Current location (i.e., index route)
        },
      ],
    },
    {
      title: "Server",
      pages: [
        {
          icon: <CubeIcon className="h-5 w-5" />,
          name: "My Server",
          path: "/admin/server",
        },
        {
          icon: <CubeTransparentIcon className="h-5 w-5" />,
          name: "Create",
          path: "/admin/create",
        },
      ],
    },
    {
      title: "Storage",
      pages: [
        {
          icon: <FolderIcon className="h-5 w-5" />,
          name: "PVC Management",
          path: "/admin/storage",
        },
      ],
    },
  ];

  return (
    <aside className="border bg-white w-64 h-screen shadow-none fixed left-0 top-0">
      <div className="p-4 h-20">
        <Typography
          variant="h5"
          color="blue-gray"
          className="text-center"
        >
          AI SOFTWARE IDE
        </Typography>
      </div>

      <nav className="p-4">
        {routes.map((section, sectionIndex) => (
          <div key={sectionIndex} className="mb-4">
            <Typography
              variant="small"
              color="blue-gray"
              className="uppercase text-xs flex text-gray-400 mb-4"
            >
              {section.title}
            </Typography>

            {section.pages.map((route, routeIndex) => (
              <NavLink
                key={routeIndex}
                to={route.path}
                className={({ isActive }) =>
                  `
                  flex items-center p-2 rounded-lg 
                  ${isActive
                    ? "bg-blue-500 text-white"
                    : "text-blue-gray-700 hover:bg-blue-50"
                  }
                  mb-1 transition-all duration-300
                `
                }
              >
                {route.icon}
                <span className="ml-3 font-medium">{route.name}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;