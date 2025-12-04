import { BrowserRouter, Switch, Route } from 'react-router-dom';
import Page1 from './Page1';
import Page2 from './Page2';
// import './App.css';
import SystemIndex from './SystemIndex';
import SystemIndexGroups from './SystemIndexGroups';
import RequestView from './RequestView';
// import RequestGantt from './RequestGantt';
import RequestTimeline from './RequestTimeline';

import "primereact/resources/themes/lara-light-blue/theme.css"; // Theme
import "primereact/resources/primereact.min.css"; // Core CSS
// import "primeicons/primeicons.css"; // Icons

import PrimeSystemIndex from './PrimeSystemIndex';
// import 'primeflex/primeflex.css';

function App() {
  return (
    <BrowserRouter>
      <Switch>
      <Route path="/systems">
          <PrimeSystemIndex />
        </Route>
        <Route path="/systemsgroups">
          <SystemIndexGroups />
        </Route>
        <Route path="/request">
          <RequestView />
        </Route>
        {/* <Route path="/gantt">
          <RequestTimeline />
        </Route> */}
        <Route path="/page2">
          <Page2 />
        </Route>
        <Route path="/">
          <Page1 />
        </Route>

      </Switch>
    </BrowserRouter>
  );
}

export default App;
