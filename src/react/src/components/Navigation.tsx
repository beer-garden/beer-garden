import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Avatar } from "primereact/avatar";
import { Menubar } from "primereact/menubar";
import { OverlayPanel } from "primereact/overlaypanel";
import { RefObject, useEffect, useRef, useState } from "react";
import { NavLink } from "react-router-dom";

import CurrentRequestsTemplate from "../components/CurrentRequestsTemplate";
import UserLogin from "../components/UserLogin";
import { Config, RequestItem, TourStepProps } from "../models/models";
import {
  ClearRefresh,
  ClearToken,
  GetRefresh,
  LogoutCurrentUser,
} from "../services/token_service";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";
import { GetCurrentUser } from "../services/user_service";
import { ClearThemes } from "../services/util_service";
import AccessButton from "./AccessButton";
import HasAccess from "./HasAccess";
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
    config?.auth_enabled === true,
  );

  const op = useRef<OverlayPanel>(null);

  const onLogout = async () => {
    await LogoutCurrentUser().catch((error) => {
      console.error("Error logging out user:", error);
    });
    updateUserName(undefined);
    runReloadUI();

    op.current?.hide();
  };

  const onClearSession = () => {
    localStorage.clear();
    sessionStorage.clear();
    ClearThemes();
    runReloadUI();
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

  const topicTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Topics Link",
    content: "Navigate to the Topics Page to see available topics.",
    layer: "NAVIGATION",
    pos: 5,
  };

  const userTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Users Link",
    content: "Navigate to the Users Page to manage users.",
    layer: "NAVIGATION",
    pos: 6,
  };

  const rolesTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Roles Link",
    content: "Navigate to the Roles Page to manage roles.",
    layer: "NAVIGATION",
    pos: 7,
  };

  const aboutTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "About Link",
    content:
      "Navigate to the About Page to see information about the application.",
    layer: "NAVIGATION",
    pos: 8,
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      (e.currentTarget as HTMLAnchorElement).click();
    }
  };

  const items = [
    {
      label: "Create Request",
      template: (item: any) => {
        return (
          <div
            role="button"
            tabIndex={0}
            onKeyDown={handleKeyDown}
            onClick={() => {
              addRequestItem();
            }}
            className="p-menuitem-link"
            {...GenerateTourProps(createRequestTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="pencil" />
            <span>{item.label}</span>
          </div>
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
            onKeyDown={handleKeyDown}
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
            onKeyDown={handleKeyDown}
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
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(workspaceTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="toolbox" />
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },

    {
      label: "Topics",

      template: (item: any) => {
        return (
          <NavLink
            to="/topics"
            className="p-menuitem-link"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(topicTourStep)}
          >
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
          <NavLink
            to="/users"
            className="p-menuitem-link"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(userTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="users" />
            <span>{item.label}</span>
          </NavLink>
        );
      },
      visible: authEnabled,
    },
    {
      label: "Roles",
      template: (item: any) => {
        return (
          <HasAccess config={config} permission="GARDEN_ADMIN" isGlobal={true}>
            <NavLink
              to="/roles"
              className="p-menuitem-link"
              onKeyDown={handleKeyDown}
              {...GenerateTourProps(rolesTourStep)}
            >
              <FontAwesomeIcon className="mr-2" icon="user-gear" />
              <span>{item.label}</span>
            </NavLink>
          </HasAccess>
        );
      },
      visible: authEnabled,
    },
    {
      label: "About",
      template: (item: any) => {
        return (
          <NavLink
            to="/about"
            className="p-menuitem-link"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(aboutTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="circle-info" />
            <span>{item.label}</span>
          </NavLink>
        );
      },
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
          <FontAwesomeIcon icon={iconDefault} aria-label="Application Icon" />
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
        const tokenUserName = GetCurrentUser();
        if (tokenUserName) {
          setUserName(tokenUserName);
        } else {
          setLoginVisible(true);
          LogoutCurrentUser().catch((error) =>
            console.error("Error logging out user:", error),
          );
        }
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
    AddTourStep(tourStepsRef, topicTourStep);
    if (authEnabled) {
      AddTourStep(tourStepsRef, userTourStep);
      AddTourStep(tourStepsRef, rolesTourStep);
    }

    AddTourStep(tourStepsRef, aboutTourStep);

    return () => {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
    };
  }, [config, authEnabled, username, iconDefault, applicationName]);

  useEffect(() => {
    if (
      authEnabled &&
      GetCurrentUser() === undefined &&
      GetRefresh() !== null
    ) {
      LogoutCurrentUser()
        .then(() => runReloadUI())
        .catch((error) => console.error("Error logging out user:", error));
    }
  }, []);

  const end = (
    <div className="flex">
      {authEnabled === true && (
        <div>
          {username === undefined && (
            <div>
              <AccessButton
                rounded
                className="mr-2"
                onClick={() => setLoginVisible(true)}
                data-testid="user-login"
                tooltip="User Login"
                label="Login"
              />
              <UserLogin
                visible={loginVisible}
                setVisible={setLoginVisible}
                setUsernameDisplay={updateUserName}
              />
            </div>
          )}
        </div>
      )}
      <AccessButton
        text
        className="mr-2"
        onClick={toggleRunTour}
        tooltip="Start Tour"
        data-testid="start-tour"
        basic
      >
        <FontAwesomeIcon className="fa-2x" icon="compass" />
      </AccessButton>

      <CurrentRequestsTemplate listeners={listeners} config={config} />
      <AccessButton
        tooltip="User Preferences Menu"
        basic
        onClick={(e) => op.current?.toggle(e)}
        text
        title="Preferences"
      >
        {username !== undefined ? (
          <Avatar
            size="large"
            label={username.charAt(0).toUpperCase()}
            style={{ width: "32px", height: "32px" }}
          />
        ) : (
          <FontAwesomeIcon icon="user" />
        )}
      </AccessButton>
      <OverlayPanel ref={op} style={{ width: "400px" }}>
        <UserOverlay
          username={username}
          onLogout={onLogout}
          onClearSession={onClearSession}
        />
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
