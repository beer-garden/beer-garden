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