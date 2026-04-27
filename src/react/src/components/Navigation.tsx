import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Avatar } from "primereact/avatar";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Menubar } from "primereact/menubar";
import { OverlayPanel } from "primereact/overlaypanel";
import { RefObject, useEffect, useRef, useState } from "react";
import { NavLink } from "react-router-dom";

import ChangeThemeDialog from "../components/ChangeThemeDialog";
import CurrentRequestsTemplate from "../components/CurrentRequestsTemplate";
import UserLogin from "../components/UserLogin";
import { Config, TourStepProps } from "../models/models";
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
  toggleRunTour,
  tourStepsRef,
}: {
  listeners: Record<string, any>;
  config: Config;
  runReloadUI: () => void;
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

  const [openThemeDialog, setOpenThemeDialog] = useState(false);
  const op = useRef(null);

  const onLogout = () => {
    ClearToken();
    ClearRefresh()
      .finally(() => {
        updateUserName(undefined);
      })
      .catch((error) => {
        console.error("Error clearing Refresh Token:", error);
      });

    op.current.hide();
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

  const requestTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Requests Link",
    content: "Navigate to the Request Page to see invoked requests.",
    layer: "NAVIGATION",
    pos: 1,
  };

  const schedulerTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Scheduler Link",
    content: "Navigate to the Scheduler Page to see scheduled jobs.",
    layer: "NAVIGATION",
    pos: 2,
  };

  const workspaceTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Workspace Link",
    content:
      "Navigate to the Workspace to see your current workbench of requests and scheduled jobs.",
    layer: "NAVIGATION",
    pos: 3,
  };

  const topicsTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Topics Link",
    content:
      "Navigate to the Topics Page to see the list of managed message bus topics.",
    layer: "NAVIGATION",
    pos: 4,
  };

  const usersTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Users Link",
    content: "Navigate to the Users Page to see the list of user accounts.",
    layer: "NAVIGATION",
    pos: 5,
  };

  const rolesTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Roles Link",
    content: "Navigate to the Roles Page to see the list of user roles.",
    layer: "NAVIGATION",
    pos: 6,
  };

  const aboutTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "About Link",
    content:
      "Navigate to the About Page to see information about this application.",
    layer: "NAVIGATION",
    pos: 7,
  };

  const items = [
    {
      label: "Requests",
      template: (item: any) => {
        return (
          <NavLink
            to="/requests"
            className="p-menuitem-link"
            {...GenerateTourProps(requestTourStep)}
          >
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
            {...GenerateTourProps(topicsTourStep)}
          >
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
            to="/"
            className="p-menuitem-link"
            {...GenerateTourProps(usersTourStep)}
          >
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "Roles",
      template: (item: any) => {
        return (
          <NavLink
            to="/roles"
            className="p-menuitem-link"
            {...GenerateTourProps(rolesTourStep)}
          >
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "About",
      template: (item: any) => {
        return (
          <NavLink
            to="/about"
            className="p-menuitem-link"
            {...GenerateTourProps(aboutTourStep)}
          >
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
    AddTourStep(tourStepsRef, requestTourStep);
    AddTourStep(tourStepsRef, schedulerTourStep);
    AddTourStep(tourStepsRef, workspaceTourStep);
    AddTourStep(tourStepsRef, topicsTourStep);
    AddTourStep(tourStepsRef, usersTourStep);
    AddTourStep(tourStepsRef, rolesTourStep);
    AddTourStep(tourStepsRef, aboutTourStep);

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
          {username !== undefined && (
            <div>
              <span className="font-bold mr-2">Welcome {username}!</span>

              <Button
                rounded
                className="mr-2"
                onClick={onLogout}
                data-testid="user-logout"
              >
                Logout
              </Button>
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

      <CurrentRequestsTemplate listeners={listeners} />
      <Button
        text
        onClick={() => setOpenThemeDialog(true)}
        tooltip="Change Theme"
        data-testid="change-theme"
      >
        <FontAwesomeIcon className="fa-2x" icon="palette" />
      </Button>
      <Button onClick={(e) => op.current.toggle(e)} text className="ml-2">
        {username !== undefined ? (
          <Avatar size="large" label={username.charAt(0).toUpperCase()} />
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
    <>
      <div className="card">
        <Dialog
          header="Change Theme"
          visible={openThemeDialog}
          onHide={() => setOpenThemeDialog(false)}
          style={{ width: "50vw" }}
        >
          <ChangeThemeDialog />
        </Dialog>
        <Menubar model={items} start={start} end={end} />
      </div>
    </>
  );
}

export default NavigationMenu;
