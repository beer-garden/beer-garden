import { GanttChart, ViewMode } from "react-modern-gantt";
// ⚠️ IMPORTANT: Don't forget to import the styles!
import 'react-modern-gantt/dist/index.css';

import { Request } from './brewtils-types';

// https://github.com/namespace-ee/react-calendar-timeline/tree/master
//const groups = [{ id: 1, title: 'group 1' }, { id: 2, title: 'group 2' }];
const groups : Array<any>= [];

// const items = [
//   {
//     id: 1,
//     group: 1,
//     title: 'item 1',
//     start_time: dayjs().valueOf(),
//     end_time: dayjs().add(1, 'hour').valueOf()
//   },
//   {
//     id: 2,
//     group: 2,
//     title: 'item 2',
//     start_time: dayjs().add(-0.5, 'hour').valueOf(),
//     end_time: dayjs().add(0.5, 'hour').valueOf()
//   },
//   {
//     id: 3,
//     group: 1,
//     title: 'item 3',
//     start_time: dayjs().add(2, 'hour').valueOf(),
//     end_time: dayjs().add(3, 'hour').valueOf()
//   }
// ];

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
    startDate: new Date(request.created_at),
    endDate: new Date(request.status_updated_at),
    progress: progress,
    dependencies: [] as Array<string>,
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

    return (<GanttChart
        tasks={items}
        viewMode={ViewMode.MINUTE}
        viewModes={[
            ViewMode.MINUTE,
            ViewMode.HOUR,
        ]}
    />)
}

export default RequestGanttHistory;