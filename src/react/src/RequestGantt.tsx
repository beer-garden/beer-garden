// import { Gantt } from "wx-react-gantt";
// import "wx-react-gantt/dist/gantt.css";
// import { Request } from './brewtils-types';

// const RequestGantt = (request: Request) => {
//     const tasks = [
//       {
//         id: 20,
//         text: "New Task",
//         start: new Date(2024, 5, 11),
//         end: new Date(2024, 6, 12),
//         duration: 1,
//         progress: 2,
//         type: "task",
//         lazy: false,
//       },
//       {
//         id: 47,
//         text: "[1] Master project",
//         start: new Date(2024, 5, 12),
//         end: new Date(2024, 7, 12),
//         duration: 8,
//         progress: 0,
//         parent: 0,
//         type: "summary",
//       },
//       {
//         id: 22,
//         text: "Task",
//         start: new Date(2024, 7, 11),
//         end: new Date(2024, 8, 12),
//         duration: 8,
//         progress: 0,
//         parent: 47,
//         type: "task",
//       },
//       {
//         id: 21,
//         text: "New Task 2",
//         start: new Date(2024, 7, 10),
//         end: new Date(2024, 8, 12),
//         duration: 3,
//         progress: 0,
//         type: "task",
//         lazy: false,
//       },
//     ];
  
//     const links = [{ id: 1, source: 20, target: 21, type: "e2e" }];
  
//     const scales = [
//       { unit: "month", step: 1, format: "MMMM yyy" },
//       { unit: "day", step: 1, format: "d" },
//     ];
  
//     return <Gantt tasks={tasks} links={links} scales={scales} />;
//   };
  
//   export default RequestGantt;


// // import { Gantt, WillowDark } from "wx-react-gantt";
// import "wx-react-gantt/dist/gantt.css";
// import { Request } from './brewtils-types';
// //     // "wx-react-gantt": "^1.3.0"
// function RequestGantt() {
//     const tasks = [
//         {
//             id: '6776dea275cff545f85a1848',
//             text: "sleep_say_sleep",
//             start: new Date(1735843490454),
//             end: new Date(1735844211479),
//             // duration: 1,
//             open: true,
//             type: "task",
//         },
//         {
//             id: '6776dea275cff545f85a184f',
//             text: "sleep",
//             start: new Date(1735843490776),
//             end: new Date(1735843850893),
//             parent: '6776dea275cff545f85a1848',
//             type: "task",
//         },
//         {
//             id: '6776e00b75cff545f85a263e',
//             text: "say",
//             start: new Date(1735843851016),
//             end: new Date(1735843851125),
//             parent: '6776dea275cff545f85a1848',
//             type: "task",
//         },
//         {
//             id: '6776e00b75cff545f85a2643',
//             text: "sleep",
//             start: new Date(1735843851197),
//             end: new Date(1735844211429),
//             parent: '6776dea275cff545f85a1848',
//             type: "task",
//         },
//     ];

//     const links = [
//         { id: 1, source: '6776dea275cff545f85a1848', target: '6776dea275cff545f85a184f', type: "s2s" },
//         { id: 2, source: '6776dea275cff545f85a1848', target: '6776e00b75cff545f85a263e', type: "s2s" },
//         { id: 3, source: '6776dea275cff545f85a1848', target: '6776e00b75cff545f85a2643', type: "s2s" },
//     ];

//     const scales = [
//         { unit: "hour", step: 60, format: "Pp" },
//     ];

//     const CustomColumn = (id: any) => {
//         return "Extract Field Later";
//     };

//     const DateToTimestamp = (date: Date) => {
//         return date.toISOString();
//     }

//     const columns = [
//         { id: "text", header: "Command", flexGrow: 2 },
//         {
//             id: "start",
//             header: "Created",
//             flexGrow: 1,
//             align: "center",
//             template: (date: Date) => DateToTimestamp(date),
//         },
//         {
//             id: "end",
//             header: "Last Updated",
//             flexGrow: 1,
//             align: "center",
//             template: (date: Date) => DateToTimestamp(date),
//         },
//         {
//             id: "id",
//             header: "Description",
//             flexGrow: 1,
//             align: "center",
//             template: (id: any) => CustomColumn(id),
//         },
//     ];
//     return <div></div>;
//     // return <WillowDark><Gantt tasks={tasks} links={links} scales={scales} columns={columns} readonly={true} /></WillowDark>;
// }


// export default RequestGantt;
export {};