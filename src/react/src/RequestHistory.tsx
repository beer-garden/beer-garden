import { faRotate } from '@fortawesome/free-solid-svg-icons';
import { Request } from './brewtils-types';
import { Table } from 'rsuite';
import 'rsuite/dist/rsuite.min.css';

function RequestHistory(request: Request) {

  const { Column, ColumnGroup, HeaderCell, Cell } = Table;

  const findNewestDate = (request: Request, newestDate: number) => {

    if (typeof request.children !== 'undefined' && request.children !== null && request.children.length > 0) {

      request.children.forEach((childRequest: Request) => {
        const childNewestDate = findNewestDate(childRequest, newestDate);
        if (childNewestDate > newestDate) {
          newestDate = childNewestDate;
        }
      });
      
    }

    if (request.status_updated_at > newestDate) {
      newestDate = request.status_updated_at;
    }

    if (request.updated_at > newestDate) {
      newestDate = request.status_updated_at;
    }

    return newestDate
  }

  // const newestDate = findNewestDate(request, request.updated_at);
  const newestDate = request.updated_at;
  const oldestDate = request.created_at;

  const timeDelta = newestDate - oldestDate;
  const timeSplit = timeDelta / 25;

  const data = [request]; 

  const columns = Array.from({ length: 28 }).map((_, index) => {

    index = index - 1;
    const indexTimestamp = oldestDate + (timeSplit * index);
    const lowerBound = indexTimestamp - (timeSplit / 2) - 1;
    const upperBound = indexTimestamp + (timeSplit / 2) + 1;

    const displayDate = new Date(indexTimestamp).toISOString();


    return {
      HeaderCell: props => {
        return <HeaderCell {...props} >{(index % 2 == 0) ? displayDate : ''}</HeaderCell>;
      },
      Cell: ({ rowData, depth, ...rest }) => {
        const colors = ['#c8f0c7', '#4cb04f', '#0f9119'];
        const startDate = rowData.created_at;
        const endDate = rowData.status_updated_at;
        // const inRange = startDate <= indexTimestamp - (timeSplit / 2) && endDate <= indexTimestamp + (timeSplit / 2);

        const justStarted = startDate >= lowerBound && startDate <= upperBound;
        const justFinished = endDate >= lowerBound && endDate <= upperBound;
        const isItRunning = startDate <= lowerBound && endDate >= upperBound;
        const inRange = justStarted || justFinished || isItRunning;
        // const inRange = startDate <= (indexTimestamp) && (indexTimestamp) <= endDate;

        if (startDate == 1735585075334) {
          console.log(`${inRange} :: ${startDate} <= ${lowerBound} && ${endDate} >= ${upperBound} == ${isItRunning}`);
        }

        return (
          <Cell
            {...rest}
            depth={depth}
            style={{
              padding: 0,
              border: 'none',
              backgroundColor: inRange ? colors[depth] : 'transparent'
            }}
          >{''}</Cell>
        );
      }
    };
  });

  return (
    <Table
      isTree
      defaultExpandAllRows
      bordered
      cellBordered
      rowKey="id"
      height={400}
      data={data}
      /** shouldUpdateScroll: whether to update the scroll bar after data update **/
      shouldUpdateScroll={false}
      onExpandChange={(isOpen, rowData) => {
        console.log(isOpen, rowData);
      }}
    >
      <Column flexGrow={1}>
        <HeaderCell>Command</HeaderCell>
        <Cell dataKey="command" />
      </Column>
      <Column>
        <HeaderCell>Status</HeaderCell>
        <Cell dataKey="status" />
      </Column>
      {columns.map((column, index) => {
        return (
          <Column key={index} width={40} align="center" verticalAlign="middle" >
            <column.HeaderCell />
            <column.Cell />
          </Column>
        );
      })}
    </Table>
  );
}

export default RequestHistory;