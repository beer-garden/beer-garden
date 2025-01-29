import { BrowserRouter, Switch, Route } from 'react-router-dom';
import Page1 from './Page1';
import Page2 from './Page2';
import './App.css';
import SystemIndex from './SystemIndex';
import SystemIndexGroups from './SystemIndexGroups';
import RequestView from './RequestView';
// import RequestGantt from './RequestGantt';

function App() {
  return (
    <BrowserRouter>
      <Switch>
      <Route path="/systems">
          <SystemIndex />
        </Route>
        <Route path="/systemsgroups">
          <SystemIndexGroups />
        </Route>
        <Route path="/request">
          <RequestView />
        </Route>
        {/* <Route path="/gantt">
          <RequestGantt />
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
