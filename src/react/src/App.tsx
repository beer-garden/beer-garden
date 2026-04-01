import "primereact/resources/themes/lara-light-blue/theme.css"; // Theme
import "primereact/resources/primereact.min.css"; // Core CSS
import "primeflex/primeflex.css";
import "./App.css";

import { PrimeReactProvider } from "primereact/api";
import { useEffect, useRef, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import AboutIndex from "./layouts/AboutIndex";
import GardenDashboard from "./layouts/Dashboard";
import JobIndex from "./layouts/JobIndex";
import RequestIndex from "./layouts/RequestIndex";
import RequestView from "./layouts/RequestView";
import RoleIndex from "./layouts/RoleIndex";
import Workspace from "./layouts/Workspace";
import { Config, Listener } from "./models/models";
import NavigationMenu from "./Navigation";
import { GetConfig } from "./services/config_service";
import { ClearSystemsCache } from "./services/system_service";
import { preemptiveRefresh } from "./services/token_service";
import { GetToken } from "./services/token_service";
import { Garden, System } from "./models/brewtils-types";
import { GetGarden, GetRootGarden } from "./services/garden_service";

function App() {
  const socketRef = useRef(null as null | any);
  const listeners = useRef<Record<string, Listener>>({});
  const [config, setConfig] = useState<Config>({});

  const [reloadUI, setReloadUI] = useState(0);

  const rootGardenRef = useRef<Garden | undefined>(sessionStorage.getItem("rootGarden") ? JSON.parse(sessionStorage.getItem("rootGarden") || "") : undefined);
  const [rootGarden, setRootGarden] = useState<Garden | undefined>(rootGardenRef.current);

  const systemsRef = useRef<System[] | undefined>(sessionStorage.getItem("systems") ? JSON.parse(sessionStorage.getItem("systems") || "") : undefined);
  const [systems, setSystems] = useState<System[] | undefined>(systemsRef.current);

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
        GetRootGarden(config).then((garden) => {
          const extractSystems = (garden: Garden): System[] => {
            let systems: System[] = [];
            if (garden.systems) {
              garden.systems.forEach((system: System) => {
                system.garden_name = garden.name;
                systems.push(system);
              });
            }
            if (garden.children) {
              for (const subGarden of garden.children) {
                systems = systems.concat(extractSystems(subGarden));
              }
            }
            return systems;
          };

          systemsRef.current = extractSystems(garden);
          setSystems(systemsRef.current);
          sessionStorage.setItem("systems", JSON.stringify(systemsRef.current));

          const removeSystems = (garden: Garden) => {
            if (garden.children) {
              garden.children = garden.children.map((child: Garden) => {              
                return removeSystems(child);
              });
            }
            return {systems, ...garden};
          }

          rootGardenRef.current = removeSystems(garden);
          setRootGarden(rootGardenRef.current);
          sessionStorage.setItem("rootGarden", JSON.stringify(rootGardenRef.current));

        }).catch((error) => {
          console.log("Unable to retrieve root garden", error);
        });
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
            <div className="flex-grow-1">
              <Routes>
                <Route
                  path="/dashboard"
                  element={<GardenDashboard listeners={listeners} />}
                />
                <Route
                  path="/request/:requestId"
                  element={
                    <RequestView listeners={listeners} config={config} />
                  }
                />
                <Route
                  path="/requests"
                  element={<RequestIndex listeners={listeners} />}
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
                  element={<JobIndex listeners={listeners} />}
                />
                <Route
                  path="/job/:jobId"
                  element={<Workspace listeners={listeners} display={false} />}
                />
                <Route path="/about" element={<AboutIndex config={config} />} />
                <Route path="/roles" element={<RoleIndex config={config} />} />
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
