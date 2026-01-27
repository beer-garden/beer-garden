import { BrowserRouter, Switch, Route } from "react-router-dom";

import RequestView from "./layouts/RequestView";
import NavigationMenu from "./Navigation";
import "primereact/resources/themes/lara-light-blue/theme.css"; // Theme
import "primereact/resources/primereact.min.css"; // Core CSS

import "primereact/resources/themes/bootstrap4-light-blue/theme.css";

import { useState, useEffect, useRef } from "react";
import RequestIndex from "./layouts/RequestIndex";
import RequestCreate from "./layouts/RequestCreate";
import JobIndex from "./layouts/JobIndex";
import SystemTable from "./layouts/SystemTable";
import GardenIndex from "./layouts/GardenIndex";
import SystemCards from "./layouts/SystemCards";
import { Divider } from "primereact/divider";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import ScratchPad from "./components/ScratchPad";
import { Listener } from "./models/models";

function App() {
  const [showScratchPad, setShowScratchPad] = useState<boolean>(false);
  const socketRef = useRef(null as null | any);
  const listeners = useRef<Record<string, Listener>>({});

  const [reloadScratchPadTrigger, setReloadScratchPadTrigger] = useState(0);

  useEffect(() => {
    // Create WebSocket connection when component mounts
    socketRef.current = new WebSocket(
      "ws://localhost:2337/api/v1/socket/events/",
    );
    const handleMessage = (event: any) => {
      // Update React state with new message
      if (event.data) {
        for (const [key, listener] of Object.entries(listeners)) {
          if (key && listener && listener.listener) {
            listener.listener(JSON.parse(event.data));
            console.log("Message from server for listener", key, event.data);
          }
        }
      }
    };
    // Add event listeners to the socket instance
    socketRef.current.addEventListener("message", handleMessage);

    // Cleanup function to run when the component unmounts or dependencies change
    return () => {
      socketRef.current.close();
    };
  }, []);

  return (
    <div>
      <NavigationMenu listeners={listeners} />
      <div className="flex">
        <div className="flex-grow-1">
          <BrowserRouter>
            <Switch>
              <Route path="/systems">
                {/* <SystemIndex /> */}
                <SystemCards />
              </Route>
              <Route path="/systemtable">
                <SystemTable />
              </Route>
              <Route path="/systemcard">
                <SystemCards />
              </Route>
              <Route path="/request/:requestId">
                <RequestView listeners={listeners} />
              </Route>
              <Route path="/requests">
                <RequestIndex
                  listeners={listeners}
                  setReloadScratchPad={setReloadScratchPadTrigger}
                />
              </Route>
              <Route path="/create/:defaultType">
                <RequestCreate />
              </Route>
              <Route path="/recreate/:requestId">
                <RequestCreate />
              </Route>
              <Route path="/jobs">
                <JobIndex />
              </Route>
              <Route path="/job/:jobId">
                <RequestCreate />
              </Route>
              <Route path="/garden">
                <GardenIndex />
              </Route>

              <Route path="/">
                <SystemCards />
              </Route>
            </Switch>
          </BrowserRouter>
        </div>
        <Divider layout="vertical">
          {showScratchPad && (
            <Button onClick={() => setShowScratchPad(false)}>
              <FontAwesomeIcon icon="angles-right" />
            </Button>
          )}
          {!showScratchPad && (
            <Button onClick={() => setShowScratchPad(true)}>
              <FontAwesomeIcon icon="angles-left" />
            </Button>
          )}
        </Divider>
        {showScratchPad && (
          <div className="flex-grow-1">
            <ScratchPad
              listeners={listeners}
              reloadTrigger={reloadScratchPadTrigger}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
