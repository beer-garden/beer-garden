import Timeline from 'react-calendar-timeline';
// make sure you include the timeline stylesheet or the timeline will not be styled
// import 'react-calendar-timeline/lib/Timeline.css';
import dayjs from 'dayjs';
import { Request } from './brewtils-types';

// https://github.com/namespace-ee/react-calendar-timeline/tree/master
const groups = [{ id: 1, title: 'group 1' }, { id: 2, title: 'group 2' }];

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

  items.push({
    id: request.id,
    group: 1,
    title: request.command,
    start_time: request.created_at,
    end_time: request.status_updated_at
  });

  // if (request.children.length > 0){
    // request.children.forEach((childRequest: Request) => {
    //   items = requestItems(childRequest, items);
    // });
    
  // }

  return items;
}

function RequestTimeline(request: Request) {

    const defaultTimeStart = request.created_at;
    const defaultTimeEnd = request.status_updated_at;

    const items = requestItems(request, []);

    return (<Timeline
      groups={groups}
      items={items}
      defaultTimeStart={defaultTimeStart}
      defaultTimeEnd={defaultTimeEnd}
    />)
}

export default RequestTimeline;