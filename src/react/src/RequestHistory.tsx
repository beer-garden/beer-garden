import { Request } from './brewtils-types';
import { CompactTable } from "@table-library/react-table-library/compact";
import { useTheme } from "@table-library/react-table-library/theme";
import { getTheme } from "@table-library/react-table-library/baseline";
import { useTree } from "@table-library/react-table-library/tree";

function RequestHistory(request: Request) {

  // const data = [request];

  const nodes = [
    {
      id: '0',
      name: 'Shopping List',
      deadline: new Date(2020, 1, 15),
      type: 'TASK',
      isComplete: true,
      nodes: 3,
    },
  ];
  
  const COLUMNS = [
    { label: 'Task', renderCell: (item) => item.name },
    {
      label: 'Deadline',
      renderCell: (item) =>
        item.deadline.toLocaleDateString('en-US', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
        }),
    },
    { label: 'Type', renderCell: (item) => item.type },
    {
      label: 'Complete',
      renderCell: (item) => item.isComplete.toString(),
    },
    { label: 'Tasks', renderCell: (item) => item.nodes },
  ];

  return (
    <CompactTable columns={COLUMNS} data={nodes} />
  );
}

export default RequestHistory;