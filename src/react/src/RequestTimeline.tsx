import Timeline from 'react-calendar-timeline';
// make sure you include the timeline stylesheet or the timeline will not be styled
import 'react-calendar-timeline/lib/Timeline.css';
import dayjs from 'dayjs';

const groups = [{ id: 1, title: 'group 1' }, { id: 2, title: 'group 2' }];

const items = [
  {
    id: 1,
    group: 1,
    title: 'item 1',
    start_time: dayjs(),
    end_time: dayjs().add(1, 'hour')
  },
  {
    id: 2,
    group: 2,
    title: 'item 2',
    start_time: dayjs().add(-0.5, 'hour'),
    end_time: dayjs().add(0.5, 'hour')
  },
  {
    id: 3,
    group: 1,
    title: 'item 3',
    start_time: dayjs().add(2, 'hour'),
    end_time: dayjs().add(3, 'hour')
  }
];

function RequestTimeline() {

  const defaultTimeStart = dayjs()
      .startOf('day')
      .valueOf()
    const defaultTimeEnd = dayjs()
      .startOf('day')
      .add(1, 'day')
      .valueOf()

    return (<Timeline
      groups={groups}
      items={items}
      defaultTimeStart={defaultTimeStart}
      defaultTimeEnd={defaultTimeEnd}
    />)
}

export default RequestTimeline;