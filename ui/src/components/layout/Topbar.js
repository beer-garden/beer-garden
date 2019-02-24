import React, { Component } from "react";
import PropTypes from "prop-types";
import { withStyles } from "@material-ui/core/styles";
import { IconButton, AppBar, Toolbar, Typography } from "@material-ui/core";
import { Menu } from "@material-ui/icons";
import UserIcon from "./UserIcon";

const styles = theme => ({
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
  },
  menuButton: {
    marginRight: 20,
    [theme.breakpoints.up("sm")]: {
      display: "none",
    },
  },
});

export class Topbar extends Component {
  state = {
    anchorEl: null,
  };

  render() {
    const {
      classes,
      appName,
      username,
      isAnonymous,
      isAuthenticated,
      setUserTheme,
      themeName,
      logout,
      authEnabled,
      toggleDrawer,
    } = this.props;

    return (
      <AppBar position="fixed" color="primary" className={classes.appBar}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="Open drawer"
            onClick={toggleDrawer}
            className={classes.menuButton}
          >
            <Menu />
          </IconButton>
          <Typography variant="h6" color="inherit" style={{ flex: 1 }}>
            {appName}
          </Typography>
          <UserIcon
            username={username}
            themeName={themeName}
            setUserTheme={setUserTheme}
            logout={logout}
            authEnabled={authEnabled}
            isAuthenticated={isAuthenticated}
            isAnonymous={isAnonymous}
          />
        </Toolbar>
      </AppBar>
    );
  }
}

Topbar.propTypes = {
  appName: PropTypes.string.isRequired,
  isAuthenticated: PropTypes.bool.isRequired,
  isAnonymous: PropTypes.bool.isRequired,
  authEnabled: PropTypes.bool.isRequired,
  classes: PropTypes.object.isRequired,
  toggleDrawer: PropTypes.func.isRequired,
  themeName: PropTypes.string,
  setUserTheme: PropTypes.func,
  logout: PropTypes.func,
  username: PropTypes.string,
};

export default withStyles(styles)(Topbar);
