
// import ReactApexChart from 'react-apexcharts'
// import { Request } from './brewtils-types';
// import React from 'react';

// function generateSeriesData(request: Request, data: Array<any>) {


    
//     data.push({
//         x: (<div><col>request.command</col><col>request.id</col></div>),
//         y: [request.created_at, request.status_updated_at]
//     });

//     if (typeof request.children !== 'undefined' && request.children !== null && request.children.length > 0) {
//         request.children.forEach((childRequest: Request) => {
//             data = generateSeriesData(childRequest, data);
//         });

//     }

//     return data;
// }


// function ApexTimeline(request: Request) {

//     const [state, setState] = React.useState({
          
//         series: [
//           {
//             data: generateSeriesData(request, [])
//           }
//         ],
//         options: {
//           chart: {
//             height: 350,
//             type: 'rangeBar'
//           },
//           plotOptions: {
//             bar: {
//               horizontal: true
//             }
//           },
//           xaxis: {
//             type: 'datetime'
//           }
//         },
      
      
//     });



//     return (
//         <div>
//             <div id="chart">
//                 <ReactApexChart options={state.options} series={state.series} type="rangeBar" height={350} />
//             </div>
//             <div id="html-dist"></div>
//         </div>
//     );
// }

// export default ApexTimeline;
export {};