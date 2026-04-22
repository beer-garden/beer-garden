import "primereact/resources/themes/lara-light-blue/theme.css"; // Theme
import "primereact/resources/primereact.min.css"; // Core CSS
import "primeflex/primeflex.css";
import "./App.css";

import { PrimeReactProvider } from "primereact/api";
import { Dialog } from "primereact/dialog";
import { useEffect, useRef, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { v4 as uuidv4 } from "uuid";

import NavigationMenu from "./components/Navigation";
import RequestItemCard from "./components/RequestItemCard";
import AboutIndex from "./layouts/AboutIndex";
import GardenDashboard from "./layouts/Dashboard";
import JobIndex from "./layouts/JobIndex";
import RequestIndex from "./layouts/RequestIndex";
import RequestView from "./layouts/RequestView";
import RoleIndex from "./layouts/RoleIndex";
import Swagger from "./layouts/Swagger";
import Workspace from "./layouts/Workspace";
import { Config, Listener, RequestItem } from "./models/models";
import { GetConfig } from "./services/config_service";
import { ClearSystemsCache } from "./services/system_service";
import { preemptiveRefresh } from "./services/token_service";
import { GetToken } from "./services/token_service";

function App() {
  const socketRef = useRef(null as null | any);
  const listeners = useRef<Record<string, Listener>>({});
  const [config, setConfig] = useState<Config>({});

  const [reloadUI, setReloadUI] = useState(0);
  const [requestItem, setRequestItem] = useState<RequestItem | undefined>(
    undefined,
  );

  const addRequestItem = (itemParams?: Partial<RequestItem>) => {
    const newItem: RequestItem = {
      itemId: uuidv4(),
      type: "REQUEST",
      ...itemParams,
    };
    setRequestItem(newItem);
  };

  const runReloadUI = () => {
    ClearSystemsCache();
    setReloadUI(reloadUI + 1);
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
              addRequestItem={addRequestItem}
            />
            {requestItem && (
              <Dialog
                visible={requestItem !== undefined}
                style={{ width: "70%", overflowY: "auto" }}
                modal
                onHide={() => {
                  setRequestItem(undefined);
                }}
                header={
                  requestItem.type === "REQUEST"
                    ? "Create Request"
                    : requestItem.type === "VIEW_REQUEST"
                      ? `View Request: ${requestItem?.requestId}`
                      : `View Scheduled Job: ${requestItem?.jobId}`
                }
              >
                <>
                  <RequestItemCard
                    removeItem={() => {
                      setRequestItem(undefined);
                    }}
                    updateRequestItem={setRequestItem}
                    requestItem={requestItem}
                    listeners={listeners}
                    addItem={addRequestItem}
                    isDialog={true}
                  />
                </>
              </Dialog>
            )}
            <div className="flex-grow-1">
              <Routes>
                <Route
                  path="/dashboard"
                  element={<GardenDashboard listeners={listeners} />}
                />
                <Route
                  path="/request/:requestId"
                  element={
                    <RequestView
                      listeners={listeners}
                      config={config}
                      addRequestItem={addRequestItem}
                    />
                  }
                />
                <Route
                  path="/requests"
                  element={
                    <RequestIndex
                      listeners={listeners}
                      addRequestItem={addRequestItem}
                    />
                  }
                />
                <Route
                  path="/create/:defaultType/:paramNamespace?/:paramSystem?/:paramVersion?/:paramInstance?/:paramCommand?"
                  element={<Workspace listeners={listeners} display={false} />}
                />
                <Route
                  path="/recreate/:requestId"
                  element={<Workspace listeners={listeners} display={false} />}
                />
                <Route
                  path="/workspace"
                  element={<Workspace listeners={listeners} />}
                />
                <Route
                  path="/workspace/request/:requestId"
                  element={<Workspace listeners={listeners} display={true} />}
                />
                <Route
                  path="/workspace/job/:jobId"
                  element={<Workspace listeners={listeners} display={true} />}
                />
                <Route
                  path="/jobs"
                  element={
                    <JobIndex
                      listeners={listeners}
                      addRequestItem={addRequestItem}
                    />
                  }
                />
                <Route
                  path="/job/:jobId"
                  element={<Workspace listeners={listeners} display={false} />}
                />
                <Route path="/about" element={<AboutIndex config={config} />} />
                <Route path="/roles" element={<RoleIndex config={config} />} />
                <Route path="/swagger" element={<Swagger />} />
                <Route
                  path="/"
                  element={<GardenDashboard listeners={listeners} />}
                />
              </Routes>
            </div>
          </BrowserRouter>
        </div>
      </div>
    </PrimeReactProvider>
  );
}

export default App;
