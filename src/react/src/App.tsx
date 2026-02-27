import "primereact/resources/themes/lara-light-blue/theme.css"; // Theme
import "primereact/resources/primereact.min.css"; // Core CSS
import "primereact/resources/themes/bootstrap4-light-blue/theme.css";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Divider } from "primereact/divider";
import { useEffect, useRef, useState } from "react";
import { BrowserRouter, Route, Switch } from "react-router-dom";

import ScratchPad from "./components/ScratchPad";
import AboutIndex from "./layouts/AboutIndex";
import GardenIndex from "./layouts/GardenIndex";
import JobIndex from "./layouts/JobIndex";
import RequestCreate from "./layouts/RequestCreate";
import RequestIndex from "./layouts/RequestIndex";
import RequestView from "./layouts/RequestView";
import SystemCards from "./layouts/SystemCards";
import SystemTable from "./layouts/SystemTable";
import { Listener } from "./models/models";
import NavigationMenu from "./Navigation";

function App() {
  const [showScratchPad, setShowScratchPad] = useState<boolean>(false);
  const [showMainApp, setShowMainApp] = useState<boolean>(true);
  const socketRef = useRef(null as null | any);
  const listeners = useRef<Record<string, Listener>>({});

  const [reloadScratchPadTrigger, setReloadScratchPadTrigger] = useState(0);

  const nagivateLeft = () => {
    if (showScratchPad && showMainApp) {
      setShowMainApp(false);
    } else if (showScratchPad && !showMainApp) {
      // Do Nothing
    } else if (!showScratchPad && showMainApp) {
      setShowScratchPad(true);
    } else if (!showScratchPad && !showMainApp) {
      // Bad State, show scratch pad
      setShowScratchPad(true);
    }
  };

  const nagivateRight = () => {
    if (showScratchPad && showMainApp) {
      setShowScratchPad(false);
    } else if (showScratchPad && !showMainApp) {
      setShowMainApp(true);
    } else if (!showScratchPad && showMainApp) {
      // Do Nothing
    } else if (!showScratchPad && !showMainApp) {
      // Bad State, show scratch pad
      setShowMainApp(true);
    }
  };

  useEffect(() => {
    // Create WebSocket connection when component mounts
    socketRef.current = new WebSocket("/api/v1/socket/events/");
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
        <div className={showMainApp ? "flex-grow-1" : "hidden"}>
          <BrowserRouter>
            <Switch>
              <Route path="/systems">
                {/* <SystemIndex /> */}
                <SystemCards setReloadScratchPad={setReloadScratchPadTrigger} />
              </Route>
              <Route path="/systemtable">
                <SystemTable />
              </Route>
              <Route path="/systemcard">
                <SystemCards setReloadScratchPad={setReloadScratchPadTrigger} />
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
              <Route path="/create/:defaultType/:paramNamespace?/:paramSystem?/:paramVersion?/:paramInstance?/:paramCommand?">
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
              <Route path="/about">
                <AboutIndex />
              </Route>

              <Route path="/">
                <SystemCards setReloadScratchPad={setReloadScratchPadTrigger} />
              </Route>
            </Switch>
          </BrowserRouter>
        </div>
        <Divider layout="vertical">
          {showScratchPad && (
            <Button onClick={() => nagivateRight()}>
              <FontAwesomeIcon icon="angles-right" />
            </Button>
          )}

          {showMainApp && (
            <Button onClick={() => nagivateLeft()}>
              <FontAwesomeIcon icon="angles-left" />
            </Button>
          )}
        </Divider>
        <div className={showScratchPad ? "flex-grow-1" : "hidden"}>
          <ScratchPad
            listeners={listeners}
            reloadTrigger={reloadScratchPadTrigger}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
