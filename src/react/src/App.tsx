import { BrowserRouter, Switch, Route } from 'react-router-dom';

// import SystemIndexGroups from './SystemIndexGroups';

import { Garden } from './models/brewtils-types';
import { System } from './models/brewtils-types';
import RequestView from './layouts/RequestView';

import "primereact/resources/themes/lara-light-blue/theme.css"; // Theme
import "primereact/resources/primereact.min.css"; // Core CSS
// import "primeicons/primeicons.css"; // Icons

import SystemIndex from './layouts/SystemIndex';
// import 'primeflex/primeflex.css';
import 'primereact/resources/themes/bootstrap4-light-blue/theme.css';

import { useState, useEffect } from 'react';
import {ExtractSystemsFromGardens} from './services/system_service';
import {GetGardenList} from './services/garden_service';
import RequestIndex from './layouts/RequestIndex';


function App() {

  // const [systems, setSystems] = useState<Array<System>>([]);
  // const [gardens, setGardens] = useState<Array<Garden>>([]);

  // useEffect(() => { 
  //   const newSystems = ExtractSystemsFromGardens(gardens, [] as Array<System>);
  //   setSystems([...newSystems]);
  // },[gardens]);

  // GetGardenList().then((data: Array<Garden>) => {
  //   setGardens(data);
  // });

  return (
    <BrowserRouter>
      <Switch>
      <Route path="/systems">
          <SystemIndex />
        </Route>
        <Route path="/request/:requestId">
          <RequestView />
        </Route>
        <Route path="/requests">
          <RequestIndex />
        </Route>

        <Route path="/">
          <SystemIndex />
        </Route>

      </Switch>
    </BrowserRouter>
  );
}

export default App;
