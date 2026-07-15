import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import MenuIcon from "@mui/icons-material/Menu";
import {
  AppBar,
  Box,
  Button,
  Container,
  IconButton,
  Link,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
} from "@mui/material";
import { Avatar } from "primereact/avatar";
import { OverlayPanel } from "primereact/overlaypanel";
import { RefObject, useEffect, useRef, useState } from "react";
import { NavLink } from "react-router-dom";

import CurrentRequestsTemplate from "../components/CurrentRequestsTemplate";
import UserLogin from "../components/UserLogin";
import { Config, RequestItem, TourStepProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
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

interface linkProps {
  label: string;
  template: (item: any) => any;
  visible?: boolean | undefined;
}

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
  const showSnackbar = useSnackbar();
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

  const [hamburgerMenuAnchor, setHamburgerMenuAnchor] = useState<
    HTMLElement | undefined
  >(undefined);
  const hamburgerMenuOpen = Boolean(hamburgerMenuAnchor);
  const handleHamburgerMenuOpen = (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    setHamburgerMenuAnchor(event.currentTarget);
  };
  const handleHamburgerMenuClose = () => {
    setHamburgerMenuAnchor(undefined);
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
          <Link
            underline="none"
            role="button"
            tabIndex={0}
            onKeyDown={handleKeyDown}
            onClick={() => {
              addRequestItem();
            }}
            {...GenerateTourProps(createRequestTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="pencil" />
            <Box component="span">{item.label}</Box>
          </Link>
        );
      },
    },
    {
      label: "Requests",
      template: (item: any) => {
        return (
          <Link component={NavLink}
            underline="none"
            to="/requests"
            className="p-menuitem-link"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(requestTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="file-lines" />
            <Box component="span" sx={{underline: "none"}}>{item.label}</Box>
          </Link>
        );
      },
    },
    {
      label: "Scheduler",
      template: (item: any) => {
        return (
          <Link component={NavLink}
            underline="none"
            to="/jobs"
            className="p-menuitem-link"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(schedulerTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="clock" />
            <span>{item.label}</span>
          </Link>
        );
      },
    },
    {
      label: "Topics",

      template: (item: any) => {
        return (
          <Link component={NavLink}
            underline="none"
            to="/topics"
            className="p-menuitem-link"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(topicTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="envelope" />
            <span>{item.label}</span>
          </Link>
        );
      },
    },

    {
      label: "Users",
      template: (item: any) => {
        return (
          <Link component={NavLink}
            underline="none"
            to="/users"
            className="p-menuitem-link"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(userTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="users" />
            <span>{item.label}</span>
          </Link>
        );
      },
      visible: authEnabled,
    },
    {
      label: "Roles",
      template: (item: any) => {
        return (
          <HasAccess config={config} permission="GARDEN_ADMIN" isGlobal={true}>
            <Link component={NavLink}
            underline="none"
              to="/roles"
              className="p-menuitem-link"
              onKeyDown={handleKeyDown}
              {...GenerateTourProps(rolesTourStep)}
            >
              <FontAwesomeIcon className="mr-2" icon="user-gear" />
              <span>{item.label}</span>
            </Link>
          </HasAccess>
        );
      },
      visible: authEnabled,
    },
    {
      label: "About",
      template: (item: any) => {
        return (
          <Link component={NavLink}
            underline="none"
            to="/about"
            className="p-menuitem-link"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(aboutTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="circle-info" />
            <span>{item.label}</span>
          </Link>
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
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error Clearing Refresh Token: ${error}`,
            life: 3000,
          });
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
    <AppBar position="static">
      <Container maxWidth={false}>
        <Toolbar
          disableGutters
          sx={{ display: "flex", alignItems: "center", gap: 2 }}
        >
          <Button
            sx={{
              whiteSpace: "nowrap",
              color: "white",
              backgroundColor: "primary.main",
              textTransform: "none",
              "&:hover": {
                backgroundColor: "primary.dark",
                opacity: [0.9, 0.8, 0.7],
              },
            }}
            component={NavLink}
            to="/"
            {...GenerateTourProps(homeLinkTourStep)}
          >
            <Box component="span" sx={{ mr: 1 }}>
              <FontAwesomeIcon
                icon={iconDefault}
                aria-label="Application Icon"
              />
            </Box>

            {applicationName && (
              <Typography className="mr-2">{applicationName}</Typography>
            )}
          </Button>

          <IconButton
            onClick={handleHamburgerMenuOpen}
            sx={{
              display: { xs: "flex", md: "none" },
              color: "white",
              backgroundColor: "primary.main",
              textTransform: "none",
              "&:hover": {
                backgroundColor: "primary.dark",
                opacity: [0.9, 0.8, 0.7],
              },
            }}
          >
            <MenuIcon />
          </IconButton>
          <Menu
            id="instance_menu"
            anchorEl={hamburgerMenuAnchor}
            anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
            transformOrigin={{ vertical: "top", horizontal: "left" }}
            open={hamburgerMenuOpen}
            onClose={handleHamburgerMenuClose}
          >
            {items
            .filter((item: linkProps) => item.visible !== false)
            .map((item: linkProps) => (
              <MenuItem key={item.label} onClick={handleHamburgerMenuClose}>{item.template(item)}</MenuItem>
            ))}
          </Menu>

          <Button
            sx={{
              display: { xs: "none", md: "flex" },
              whiteSpace: "nowrap",
              color: "white",
              backgroundColor: "primary.main",
              textTransform: "none",
              "&:hover": {
                backgroundColor: "primary.dark",
                opacity: [0.9, 0.8, 0.7],
              },
            }}
            role="button"
            tabIndex={0}
            onKeyDown={handleKeyDown}
            onClick={() => {
              addRequestItem();
            }}
            {...GenerateTourProps(createRequestTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="pencil" />
            <Box component="span">Create Request</Box>
          </Button>
          <Button
            sx={{
              display: { xs: "none", md: "flex" },
              whiteSpace: "nowrap",
              color: "white",
              backgroundColor: "primary.main",
              textTransform: "none",
              "&:hover": {
                backgroundColor: "primary.dark",
                opacity: [0.9, 0.8, 0.7],
              },
            }}
            component={NavLink}
            to="/requests"
            role="button"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(requestTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="file-lines" />
            <Box component="span">Requests</Box>
          </Button>
          <Button
            sx={{
              display: { xs: "none", md: "flex" },
              whiteSpace: "nowrap",
              color: "white",
              backgroundColor: "primary.main",
              textTransform: "none",
              "&:hover": {
                backgroundColor: "primary.dark",
                opacity: [0.9, 0.8, 0.7],
              },
            }}
            component={NavLink}
            to="/jobs"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(schedulerTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="clock" />
            <Box component="span">Scheduler</Box>
          </Button>
          <Button
            sx={{
              display: { xs: "none", md: "flex" },
              whiteSpace: "nowrap",
              color: "white",
              backgroundColor: "primary.main",
              textTransform: "none",
              "&:hover": {
                backgroundColor: "primary.dark",
                opacity: [0.9, 0.8, 0.7],
              },
            }}
            component={NavLink}
            to="/topics"
            className="p-menuitem-link"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(topicTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="envelope" />
            <Box component="span">Topics</Box>
          </Button>
          {authEnabled === true && (
            <Button
              sx={{
                display: { xs: "none", md: "flex" },
                whiteSpace: "nowrap",
                color: "white",
                backgroundColor: "primary.main",
                textTransform: "none",
                "&:hover": {
                  backgroundColor: "primary.dark",
                  opacity: [0.9, 0.8, 0.7],
                },
              }}
              component={NavLink}
              to="/users"
              className="p-menuitem-link"
              onKeyDown={handleKeyDown}
              {...GenerateTourProps(userTourStep)}
            >
              <FontAwesomeIcon className="mr-2" icon="users" />
              <Box component="span">Users</Box>
            </Button>
          )}
          {authEnabled === true && (
            <HasAccess
              config={config}
              permission="GARDEN_ADMIN"
              isGlobal={true}
            >
              <Button
                sx={{
                  display: { xs: "none", md: "flex" },
                  whiteSpace: "nowrap",
                  color: "white",
                  backgroundColor: "primary.main",
                  textTransform: "none",
                  "&:hover": {
                    backgroundColor: "primary.dark",
                    opacity: [0.9, 0.8, 0.7],
                  },
                }}
                component={NavLink}
                to="/roles"
                onKeyDown={handleKeyDown}
                {...GenerateTourProps(rolesTourStep)}
              >
                <FontAwesomeIcon className="mr-2" icon="user-gear" />
                <Box component="span">Roles</Box>
              </Button>
            </HasAccess>
          )}
          <Button
            sx={{
              display: { xs: "none", md: "flex" },
              whiteSpace: "nowrap",
              color: "white",
              backgroundColor: "primary.main",
              textTransform: "none",
              "&:hover": {
                backgroundColor: "primary.dark",
                opacity: [0.9, 0.8, 0.7],
              },
            }}
            component={NavLink}
            to="/about"
            className="p-menuitem-link"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(aboutTourStep)}
          >
            <FontAwesomeIcon className="mr-2" icon="circle-info" />
            <Box component="span">About</Box>
          </Button>
          <Box sx={{ ml: "auto" }} />
          {authEnabled === true && (
            <>
              {username === undefined && (
                <>
                  <AccessButton
                    sx={{ borderRadius: 20 }}
                    color="secondary"
                    className="mr-2"
                    onClick={() => setLoginVisible(true)}
                    data-testid="user-login"
                    tooltip="User Login"
                    label="Login"
                  >
                    Login{" "}
                  </AccessButton>
                  <UserLogin
                    visible={loginVisible}
                    setVisible={setLoginVisible}
                    setUsernameDisplay={updateUserName}
                  />
                </>
              )}
            </>
          )}
          <Box sx={{ display: "flex", alignItems: "center", gap: 0 }}>
            <AccessButton
              sx={{ height: "36px" }}
              color="secondary"
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
              sx={{ height: "36px" }}
              color="secondary"
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
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}

export default NavigationMenu;
