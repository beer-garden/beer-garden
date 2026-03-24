import "primereact/resources/themes/lara-light-blue/theme.css"; // Theme
import "primereact/resources/primereact.min.css"; // Core CSS
import "primereact/resources/themes/bootstrap4-light-blue/theme.css";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { PrimeReactProvider } from "primereact/api";
import { Button } from "primereact/button";
import { Divider } from "primereact/divider";
import { useEffect, useRef, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import ScratchPad from "./components/ScratchPad";
import AboutIndex from "./layouts/AboutIndex";
import GardenIndex from "./layouts/GardenIndex";
import JobIndex from "./layouts/JobIndex";
import RequestCreate from "./layouts/RequestCreate";
import RequestIndex from "./layouts/RequestIndex";
import RequestView from "./layouts/RequestView";
import SystemCards from "./layouts/SystemCards";
import SystemTable from "./layouts/SystemTable";
import { Config, Listener } from "./models/models";
import NavigationMenu from "./Navigation";
import { GetConfig } from "./services/config_service";
import { ClearSystemsCache } from "./services/system_service";
import { preemptiveRefresh } from "./services/token_service";
import { GetToken } from "./services/token_service";

function App() {
  const [showScratchPad, setShowScratchPad] = useState<boolean>(false);
  const [showMainApp, setShowMainApp] = useState<boolean>(true);
  const socketRef = useRef(null as null | any);
  const listeners = useRef<Record<string, Listener>>({});
  const [config, setConfig] = useState<Config>({});

  const [reloadScratchPadTrigger, setReloadScratchPadTrigger] = useState(0);
  const [reloadUI, setReloadUI] = useState(0);

  const runReloadUI = () => {
    ClearSystemsCache();
    setReloadUI((prev) => prev + 1);
  };

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

  const primeValue = {
    hideOverlaysOnDocumentScrolling: true,
  };

  useEffect(() => {
    GetConfig()
      .then((config) => {
        setConfig(config);
      })
      .catch((error) => {
        console.log("Unable to retrieve configuration", error);
      });

    const interval = setInterval(preemptiveRefresh, 30000);

    // Cleanup function to clear the interval when the component unmounts
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Create WebSocket connection when component mounts
    socketRef.current = new WebSocket("/api/v1/socket/events/");
    const handleMessage = (event: any) => {
      // Update React state with new message

      if (event.data) {
        const eventData = JSON.parse(event.data);
        if (eventData?.name === "AUTHORIZATION_REQUIRED") {
          socketRef.current.send(
            JSON.stringify({ name: "UPDATE_TOKEN", payload: GetToken() }),
          );
        } else {
          for (const [key, listener] of Object.entries(listeners)) {
            if (key && listener && listener.listener) {
              listener.listener(eventData);
              console.log("Message from server for listener", key, event.data);
            }
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

  const baseURL =
    import.meta.env.VITE_BASE_URL === "/"
      ? undefined
      : import.meta.env.VITE_BASE_URL || undefined;

  return (
    <PrimeReactProvider value={primeValue}>
      <div className="flex">
        <div className="flex-grow-1">
          <BrowserRouter basename={baseURL}>
            <NavigationMenu
              listeners={listeners}
              config={config}
              runReloadUI={runReloadUI}
            />
            <div className="flex" key={reloadUI}>
              <div className={showMainApp ? "flex-grow-1" : "hidden"}>
                <Routes>
                  <Route
                    path="/systems"
                    element={
                      <SystemCards
                        listeners={listeners}
                        setReloadScratchPad={setReloadScratchPadTrigger}
                      />
                    }
                  />
                  <Route path="/systemtable" element={<SystemTable />} />
                  <Route
                    path="/systemcard"
                    element={
                      <SystemCards
                        listeners={listeners}
                        setReloadScratchPad={setReloadScratchPadTrigger}
                      />
                    }
                  />
                  <Route
                    path="/request/:requestId"
                    element={
                      <RequestView listeners={listeners} config={config} />
                    }
                  />
                  <Route
                    path="/requests"
                    element={
                      <RequestIndex
                        listeners={listeners}
                        setReloadScratchPad={setReloadScratchPadTrigger}
                      />
                    }
                  />
                  <Route
                    path="/create/:defaultType/:paramNamespace?/:paramSystem?/:paramVersion?/:paramInstance?/:paramCommand?"
                    element={<RequestCreate config={config} />}
                  />
                  <Route
                    path="/recreate/:requestId"
                    element={<RequestCreate config={config} />}
                  />
                  <Route path="/jobs" element={<JobIndex />} />
                  <Route
                    path="/job/:jobId"
                    element={<RequestCreate config={config} />}
                  />
                  <Route
                    path="/garden"
                    element={
                      <GardenIndex listeners={listeners} config={config} />
                    }
                  />

                  <Route
                    path="/about"
                    element={<AboutIndex config={config} />}
                  />
                  <Route
                    path="/"
                    element={
                      <SystemCards
                        listeners={listeners}
                        setReloadScratchPad={setReloadScratchPadTrigger}
                      />
                    }
                  />
                </Routes>
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
          </BrowserRouter>
        </div>
      </div>
    </PrimeReactProvider>
  );
}

export default App;
