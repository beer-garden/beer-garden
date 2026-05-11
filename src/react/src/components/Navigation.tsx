import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Avatar } from "primereact/avatar";
import { Button } from "primereact/button";
import { Menubar } from "primereact/menubar";
import { OverlayPanel } from "primereact/overlaypanel";
import { RefObject, useEffect, useRef, useState } from "react";
import { NavLink } from "react-router-dom";

import CurrentRequestsTemplate from "../components/CurrentRequestsTemplate";
import UserLogin from "../components/UserLogin";
import { Config, RequestItem, TourStepProps } from "../models/models";
import { ClearRefresh, ClearToken } from "../services/token_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { GetCurrentUser } from "../services/user_service";
import UserOverlay from "./UserOverlay";

function NavigationMenu({
  listeners,
  config,
  runReloadUI,
  addRequestItem,
  toggleRunTour,
  tourStepsRef,
}: {
  listeners: Record<string, any>;
  config: Config;
  runReloadUI: () => void;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
  toggleRunTour: () => void;
  tourStepsRef: RefObject<Array<TourStepProps>>;
}) {
  const [iconDefault, setIconDefault] = useState<string>(
    config?.icon_default ?? "beer-mug-empty",
  );
  const [applicationName, setApplicationName] = useState<string | undefined>(
    config?.application_name,
  );
  const [authEnabled, setAuthEnabled] = useState<boolean | undefined>(
    config?.auth_enabled,
  );

  const op = useRef<OverlayPanel>(null);

  const onLogout = () => {
    ClearToken();
    ClearRefresh()
      .finally(() => {
        updateUserName(undefined);
      })
      .catch((error) => {
        console.error("Error clearing Refresh Token:", error);
      });

    op.current?.hide();
  };

  const tourUuid = "navigation_tour";
  const tourPrefix = "navigation";

  const homeLinkTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Home Link",
    content: "Navigate to the home page of the application.",
    layer: "NAVIGATION",
    pos: 0,
  };

  const createRequestTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Create Request Link",
    content: "Open popup to create a new request.",
    layer: "NAVIGATION",
    pos: 1,
  };

  const requestTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Requests Link",
    content: "Navigate to the Request Page to see invoked requests.",
    layer: "NAVIGATION",
    pos: 2,
  };

  const schedulerTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Scheduler Link",
    content: "Navigate to the Scheduler Page to see scheduled jobs.",
    layer: "NAVIGATION",
    pos: 3,
  };

  const workspaceTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Workspace Link",
    content:
      "Navigate to the Workspace to see your current workbench of requests and scheduled jobs.",
    layer: "NAVIGATION",
    pos: 4,
  };

  const items = [
    {
      label: "Create Request",
      template: (item: any) => {
        return (
          <NavLink
            to="/requests"
            onClick={(e) => {
              e.preventDefault();
              addRequestItem();
            }}
            className="p-menuitem-link"
            {...GenerateTourProps(createRequestTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="pencil" />
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "Requests",
      template: (item: any) => {
        return (
          <NavLink
            to="/requests"
            className="p-menuitem-link"
            {...GenerateTourProps(requestTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="file-lines" />
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "Scheduler",
      template: (item: any) => {
        return (
          <NavLink
            to="/jobs"
            className="p-menuitem-link"
            {...GenerateTourProps(schedulerTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="clock" />
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "Workspace",
      template: (item: any) => {
        return (
          <NavLink
            to="/workspace"
            className="p-menuitem-link"
            {...GenerateTourProps(workspaceTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="toolbox" />
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "Admin",
      icon: <FontAwesomeIcon className="mr-2" icon="bars" />,
      items: [
        {
          label: "Topics",

          template: (item: any) => {
            return (
              <NavLink to="/topics" className="p-menuitem-link">
                <FontAwesomeIcon className="mr-2" icon="envelope" />
                <span>{item.label}</span>
              </NavLink>
            );
          },
        },
        {
          label: "Users",
          template: (item: any) => {
            return (
              <NavLink to="/users" className="p-menuitem-link">
                <FontAwesomeIcon className="mr-2" icon="users" />
                <span>{item.label}</span>
              </NavLink>
            );
          },
        },
        {
          label: "Roles",
          template: (item: any) => {
            return (
              <NavLink to="/roles" className="p-menuitem-link">
                <FontAwesomeIcon className="mr-2" icon="user-gear" />
                <span>{item.label}</span>
              </NavLink>
            );
          },
        },

        {
          label: "About",
          template: (item: any) => {
            return (
              <NavLink to="/about" className="p-menuitem-link">
                <FontAwesomeIcon className="mr-2" icon="circle-info" />
                <span>{item.label}</span>
              </NavLink>
            );
          },
        },
      ],
    },
  ];

  const start = (
    <NavLink
      className="p-menuitem-link text-primary cursor-pointer px-3 py-2 overflow-hidden relative font-semibold text-lg uppercase p-ripple hover:surface-ground"
      to="/"
      {...GenerateTourProps(homeLinkTourStep)}
    >
      <div className="flex">
        <div className="mr-2">
          <FontAwesomeIcon icon={iconDefault} />
        </div>

        {applicationName && <div className="mr-2">{applicationName}</div>}
      </div>
    </NavLink>
  );

  const getUserName = () => {
    if (authEnabled === true) {
      return GetCurrentUser();
    }
    return undefined;
  };

  const [username, setUserName] = useState<string | undefined>(getUserName());
  const [loginVisible, setLoginVisible] = useState(false);

  const updateUserName = (username: string | undefined) => {
    setUserName(username);
    runReloadUI();
  };

  useEffect(() => {
    if (config?.icon_default && config.icon_default !== iconDefault) {
      setIconDefault(config.icon_default);
    }

    if (
      config?.application_name &&
      config.application_name !== applicationName
    ) {
      setApplicationName(config.application_name);
    }

    if (
      config?.auth_enabled !== undefined &&
      config.auth_enabled !== authEnabled
    ) {
      setAuthEnabled(config.auth_enabled);
      if (config.auth_enabled && username === undefined) {
        setLoginVisible(true);
      } else if (!config.auth_enabled) {
        ClearToken();
        ClearRefresh().catch((error) => {
          console.error("Error Clearing Refresh Token:", error);
        });
      }
    }

    AddTourStep(tourStepsRef, homeLinkTourStep);
    AddTourStep(tourStepsRef, createRequestTourStep);
    AddTourStep(tourStepsRef, requestTourStep);
    AddTourStep(tourStepsRef, schedulerTourStep);
    AddTourStep(tourStepsRef, workspaceTourStep);

    return () => {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
    };
  }, [config, authEnabled, username, iconDefault, applicationName]);

  const end = (
    <div className="flex">
      {authEnabled === true && (
        <div>
          {username === undefined && (
            <div>
              <Button
                rounded
                className="mr-2"
                onClick={() => setLoginVisible(true)}
                data-testid="user-login"
              >
                Login
              </Button>
              <UserLogin
                visible={loginVisible}
                setVisible={setLoginVisible}
                setUsernameDisplay={updateUserName}
              />
            </div>
          )}
        </div>
      )}
      <Button
        text
        className="mr-2"
        onClick={toggleRunTour}
        aria-label="Start Tour"
        title="Start Tour"
        data-testid="start-tour"
      >
        <FontAwesomeIcon className="fa-2x" icon="compass" />
      </Button>

      <CurrentRequestsTemplate listeners={listeners} config={config} />
      <Button onClick={(e) => op.current?.toggle(e)} text>
        {username !== undefined ? (
          <Avatar
            size="large"
            label={username.charAt(0).toUpperCase()}
            style={{ width: "32px", height: "32px" }}
          />
        ) : (
          <FontAwesomeIcon icon="user" />
        )}
      </Button>
      <OverlayPanel ref={op} style={{ width: "400px" }}>
        <UserOverlay username={username} onLogout={onLogout} />
      </OverlayPanel>
    </div>
  );

  return (
    <div className="card">
      <Menubar model={items} start={start} end={end} />
    </div>
  );
}

export default NavigationMenu;
