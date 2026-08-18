import { IconProp } from "@fortawesome/fontawesome-svg-core";
import {
  AppBar,
  Avatar,
  Box,
  Button,
  ClickAwayListener,
  Container,
  IconButton,
  Link,
  Menu,
  MenuItem,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";
import Fade from "@mui/material/Fade";
import Popper from "@mui/material/Popper";
import { RefObject, useEffect, useState } from "react";
import React from "react";
import { NavLink } from "react-router-dom";

import CurrentRequestsTemplate from "../components/CurrentRequestsTemplate";
import UserLogin from "../components/UserLogin";
import { Config, RequestItem, TourStepProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { checkPermission } from "../services/permission_service";
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
import { ClearThemes, FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";
import UserOverlay from "./UserOverlay";

interface linkProps {
  label: string;
  buttonTemplate: () => any;
  linkTemplate: () => any;
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

  const onLogout = async () => {
    await LogoutCurrentUser().catch((error) => {
      console.error("Error logging out user:", error);
    });
    updateUserName(undefined);
    runReloadUI();
  };

  const onClearSession = () => {
    localStorage.clear();
    sessionStorage.clear();
    ClearThemes();
    runReloadUI();
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

  const topicTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Topics Link",
    content: "Navigate to the Topics Page to see available topics.",
    layer: "NAVIGATION",
    pos: 4,
  };

  const userTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Users Link",
    content: "Navigate to the Users Page to manage users.",
    layer: "NAVIGATION",
    pos: 5,
  };

  const rolesTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Roles Link",
    content: "Navigate to the Roles Page to manage roles.",
    layer: "NAVIGATION",
    pos: 6,
  };

  const aboutTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "About Link",
    content:
      "Navigate to the About Page to see information about the application.",
    layer: "NAVIGATION",
    pos: 7,
  };

  const [userPopperOpen, setUserPopperOpen] = React.useState(false);
  const [userPopperAnchorEl, setUserPopperAnchorEl] =
    React.useState<null | HTMLElement>(null);

  const handleUserPopperOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserPopperAnchorEl(event.currentTarget);
    setUserPopperOpen(true);
  };

  const handleUserPopperClickAway = () => {
    setUserPopperOpen(false);
  };

  const canBeOpen = userPopperOpen && Boolean(userPopperAnchorEl);
  const userPopperId = canBeOpen ? "userPopper" : undefined;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      (e.currentTarget as HTMLAnchorElement).click();
    }
  };

  const navButtonStyles = {
    display: { xs: "none", md: "flex" },
    whiteSpace: "nowrap",
    color: "inherit",
    textTransform: "none",
    "&:hover": {
      backgroundColor: "primary.dark",
      opacity: [0.9, 0.8, 0.7],
    },
  };

  const items = [
    {
      label: "Create Request",
      buttonTemplate: () => {
        return (
          <Button
            sx={navButtonStyles}
            role="button"
            tabIndex={0}
            onKeyDown={handleKeyDown}
            onClick={() => {
              addRequestItem();
            }}
            {...GenerateTourProps(createRequestTourStep)}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="pencil" />
              <Box component="span">Create Request</Box>
            </Stack>
          </Button>
        );
      },
      linkTemplate: () => {
        return (
          <Link
            underline="none"
            role="button"
            tabIndex={0}
            onKeyDown={handleKeyDown}
            onClick={() => {
              addRequestItem();
            }}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="pencil" />
              <Box component="span">Create Request</Box>
            </Stack>
          </Link>
        );
      },
    },
    {
      label: "Requests",
      buttonTemplate: () => {
        return (
          <Button
            sx={navButtonStyles}
            component={NavLink}
            to="/requests"
            role="button"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(requestTourStep)}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="file-lines" />
              <Box component="span">Requests</Box>
            </Stack>
          </Button>
        );
      },
      linkTemplate: () => {
        return (
          <Link
            component={NavLink}
            underline="none"
            to="/requests"
            onKeyDown={handleKeyDown}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="file-lines" />
              <Box component="span">Requests</Box>
            </Stack>
          </Link>
        );
      },
    },
    {
      label: "Scheduler",
      buttonTemplate: () => {
        return (
          <Button
            sx={navButtonStyles}
            component={NavLink}
            to="/jobs"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(schedulerTourStep)}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="clock" />
              <Box component="span">Scheduler</Box>
            </Stack>
          </Button>
        );
      },
      linkTemplate: () => {
        return (
          <Link
            component={NavLink}
            underline="none"
            to="/jobs"
            onKeyDown={handleKeyDown}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="clock" />
              <Box component="span">Scheduler</Box>
            </Stack>
          </Link>
        );
      },
    },
    {
      label: "Topics",
      buttonTemplate: () => {
        return (
          <Button
            sx={navButtonStyles}
            component={NavLink}
            to="/topics"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(topicTourStep)}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="envelope" />
              <Box component="span">Topics</Box>
            </Stack>
          </Button>
        );
      },
      linkTemplate: () => {
        return (
          <Link
            component={NavLink}
            underline="none"
            to="/topics"
            onKeyDown={handleKeyDown}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="envelope" />
              <Box component="span">Topics</Box>
            </Stack>
          </Link>
        );
      },
    },

    {
      label: "Users",
      buttonTemplate: () => {
        return (
          <Button
            sx={navButtonStyles}
            component={NavLink}
            to="/users"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(userTourStep)}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="users" />
              <Box component="span">Users</Box>
            </Stack>
          </Button>
        );
      },
      linkTemplate: () => {
        return (
          <Link
            component={NavLink}
            underline="none"
            to="/users"
            onKeyDown={handleKeyDown}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="users" />
              <Box component="span">Users</Box>
            </Stack>
          </Link>
        );
      },
      visible: authEnabled,
    },
    {
      label: "Roles",
      buttonTemplate: () => {
        return (
          <Button
            sx={navButtonStyles}
            component={NavLink}
            to="/roles"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(rolesTourStep)}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="user-gear" />
              <Box component="span">Roles</Box>
            </Stack>
          </Button>
        );
      },
      linkTemplate: () => {
        return (
          <Link
            component={NavLink}
            underline="none"
            to="/roles"
            onKeyDown={handleKeyDown}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="user-gear" />
              <Box component="span">Roles</Box>
            </Stack>
          </Link>
        );
      },
      visible: authEnabled && checkPermission(config, "GARDEN_ADMIN", {}),
    },
    {
      label: "About",
      buttonTemplate: () => {
        return (
          <Button
            sx={navButtonStyles}
            component={NavLink}
            to="/about"
            onKeyDown={handleKeyDown}
            {...GenerateTourProps(aboutTourStep)}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="circle-info" />
              <Box component="span">About</Box>
            </Stack>
          </Button>
        );
      },
      linkTemplate: () => {
        return (
          <Link
            component={NavLink}
            underline="none"
            to="/about"
            onKeyDown={handleKeyDown}
          >
            <Stack direction="row" spacing={1}>
              <FAIcon icon="circle-info" />
              <Box component="span">About</Box>
            </Stack>
          </Link>
        );
      },
    },
  ];

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

  return (
    <AppBar position="static" sx={{bgcolor:"primary.main"}}>
      <Container maxWidth={false}>
        <Toolbar
          disableGutters
          sx={{ display: "flex", alignItems: "center", gap: 2 }}
        >
          <Button
            sx={navButtonStyles}
            component={NavLink}
            to="/"
            {...GenerateTourProps(homeLinkTourStep)}
          >
            <FAIcon
              icon={iconDefault as IconProp}
              aria-label="Application Icon"
              sx={{ mr: 1 }}
            />

            {applicationName && (
              <Typography sx={{ mr: 1 }}>{applicationName}</Typography>
            )}
          </Button>

          <IconButton
            onClick={handleHamburgerMenuOpen}
            aria-label="Open navigation menu"
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
            <FAIcon icon="bars" sx={{ fontSize: 16, px: "4px" }} />
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
                <MenuItem key={item.label} onClick={handleHamburgerMenuClose}>
                  {item.linkTemplate()}
                </MenuItem>
              ))}
          </Menu>

          {items
            .filter((item: linkProps) => item.visible !== false)
            .map((item: linkProps) => (
              <span key={item.label}>{item.buttonTemplate()}</span>
            ))}

          <Box sx={{ ml: "auto" }} />
          {authEnabled === true && (
            <>
              {username === undefined && (
                <>
                  <AccessButton
                    sx={{ borderRadius: 20, mr: 1 }}
                    color="secondary"
                    onClick={() => setLoginVisible(true)}
                    data-testid="user-login"
                    tooltip="User Login"
                    label="Login"
                  >
                    Login
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
              sx={{ height: "36px", color: "primary.contrastText", mr: 2 }}
              text
              onClick={toggleRunTour}
              tooltip="Start Tour"
              data-testid="start-tour"
              basic
            >
              <FAIcon sx={{ fontSize: 24 }} icon="compass" />
            </AccessButton>
            <CurrentRequestsTemplate listeners={listeners} config={config} />
            <AccessButton
              sx={{ height: "36px", color: "primary.contrastText" }}
              tooltip="User Preferences Menu"
              basic
              onClick={handleUserPopperOpen}
              text
              title="Preferences"
            >
              {username !== undefined ? (
                <Avatar variant="square" sx={{ width: "32px", height: "32px" }}>
                  {username.charAt(0).toUpperCase()}
                </Avatar>
              ) : (
                <FAIcon icon="user" />
              )}
            </AccessButton>
            <Popper
              sx={{ zIndex: 1000 }}
              disablePortal
              id={userPopperId}
              open={userPopperOpen}
              anchorEl={userPopperAnchorEl}
              transition
              placement="bottom-end"
              modifiers={[
                {
                  name: "offset",
                  options: {
                    offset: [0, 15], // [X-offset, Y-offset] in pixels
                  },
                },
              ]}
            >
              {({ TransitionProps }) => (
                <ClickAwayListener onClickAway={handleUserPopperClickAway}>
                  <Fade {...TransitionProps} timeout={350}>
                    <Box
                      sx={{
                        width: "400px",
                        boxShadow: 3,
                        p: 1,
                        bgcolor: "background.paper",
                      }}
                    >
                      <UserOverlay
                        username={username}
                        onLogout={onLogout}
                        onClearSession={onClearSession}
                      />
                    </Box>
                  </Fade>
                </ClickAwayListener>
              )}
            </Popper>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}

export default NavigationMenu;
