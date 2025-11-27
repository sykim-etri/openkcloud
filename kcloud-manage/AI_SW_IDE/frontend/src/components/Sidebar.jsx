import {
  Card,
  Typography,
  List,
  ListItem,
  ListItemPrefix,
  ListItemSuffix,
  Chip,
} from "@material-tailwind/react";
import {
  PresentationChartBarIcon,
  CubeIcon
} from "@heroicons/react/24/solid";
 
export function Sidebar({ onSelect }) {
  return (
    <Card className="top-5 left-5 h-[calc(90vh-2rem)] min-w-[270px] w-full max-w-[17rem] p-6 shadow-xl shadow-blue-gray-900/5 border border-gray-300 rounded-xl">
      <div className="mb-2 p-10">
        <img src="/assets/ai_lab.png" alt="AI Lab Logo" className="h-[80px] w-[160px]" />
      </div>
      <List>
      <ListItem onClick={() => onSelect("status")} className="cursor-pointer">
          <ListItemPrefix>
            <PresentationChartBarIcon className="h-10 w-5" />
          </ListItemPrefix>
          Usage Status
        </ListItem>
        <ListItem onClick={() => onSelect("pod")} className="cursor-not-allowed opacity-50">
          <ListItemPrefix>
            <CubeIcon className="h-10 w-5" />
          </ListItemPrefix>
          Create Server
        </ListItem>
        
      </List>
    </Card>
  );
}



export default Sidebar;