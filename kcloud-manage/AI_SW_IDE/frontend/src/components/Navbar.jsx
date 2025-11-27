import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Navbar,
  Collapse,
  Typography,
  Button,
  IconButton,
  Card,
} from "@material-tailwind/react";
import { ArrowRightOnRectangleIcon, UserCircleIcon } from "@heroicons/react/24/solid";
import { logout, getCurrentUser } from "@/utils/auth";
 
export function StickyNavbar() {
  const [openNav, setOpenNav] = React.useState(false);
  const navigate = useNavigate();
  const currentUser = getCurrentUser();
 
  React.useEffect(() => {
    window.addEventListener(
      "resize",
      () => window.innerWidth >= 960 && setOpenNav(false)
    );
  }, []);

  const handleLogout = () => {
    if (confirm("Are you sure you want to logout?")) {
      logout();
    }
  };
 
  return (
    <div className="w-[calc(100%)]">
      <Navbar className="border border-l-0 sticky top-0 z-10 h-max max-w-full rounded-none shadow-none lg:px-8 lg:py-4">
        <div className="flex items-center justify-between text-blue-gray-900">
          <Typography
            as="a"
            href="#"
            className="mr-4 cursor-pointer py-1.5 font-medium"
          >
            AI SOFTWARE IDE
          </Typography>
          
          {/* Top right user information and logout button */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-blue-gray-600">
              <UserCircleIcon className="h-5 w-5" />
              <span>{currentUser?.username || "User"}</span>
            </div>
            
            <Button
              variant="outlined"
              size="sm"
              className="flex items-center gap-2 hover:bg-red-50 hover:border-red-300 hover:text-red-700"
              onClick={handleLogout}
            >
              <ArrowRightOnRectangleIcon className="h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </Navbar>
    </div>
  );
}