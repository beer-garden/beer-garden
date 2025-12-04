import { GanttChart, ViewMode } from "react-modern-gantt";
// ⚠️ IMPORTANT: Don't forget to import the styles!
import 'react-modern-gantt/dist/index.css';

import { Request } from './brewtils-types';


function requestItems(request: Request, items: Array<any>) {

  let progress = 0;
    if (request.status == 'COMPLETED') {
        progress = 100;
    } else if (request.status == 'FAILED' || request.status == 'CANCELED') {
        progress = 100;
    } else if (request.status == "IN_PROGRESS") {
        progress = 50;
    }

  let requestTask = {
    id: request.id,
    name: request.command,
    // startDate: new Date(2023, 1, 1, 6, 23, 45),  // Placeholder start date
    // endDate: new Date(2023, 1, 1, 23, 29, 4),
    startDate: new Date(request.created_at),
    endDate: new Date(request.status_updated_at),
    progress: progress,
    dependencies: [] as Array<string>,
    color: '#3b82f6',
  };


  if (typeof request.children !== 'undefined' && request.children !== null && request.children.length > 0) {

    request.children.forEach((childRequest: Request) => {
        items = requestItems(childRequest, items);
        if (childRequest.id) {
            requestTask.dependencies.push(childRequest.id);
        }
    });
    
  }
  items.push(requestTask);
  return items;
}

function RequestGanttHistory(request: Request) {

    const items = requestItems(request, []);

    const taskGroup = {
        id: 'requests',
        name: 'Requests',
        tasks: items,
    }


    return (<GanttChart
        tasks={[taskGroup]}
        viewMode={ViewMode.MINUTE}
        viewModes={[
            ViewMode.MINUTE,
            ViewMode.HOUR,
        ]}
    />)
}

export default RequestGanttHistory;