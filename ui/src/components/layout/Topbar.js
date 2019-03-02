import React, { Component } from "react";
import PropTypes from "prop-types";
import { Link as RouterLink } from "react-router-dom";
import { withStyles } from "@material-ui/core/styles";
import AppBar from "@material-ui/core/AppBar";
import IconButton from "@material-ui/core/IconButton";
import Toolbar from "@material-ui/core/Toolbar";
import Link from "@material-ui/core/Link";
import Menu from "@material-ui/icons/Menu";
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
          <Link
            component={RouterLink}
            underline="none"
            to="/"
            variant="h6"
            color="inherit"
            style={{ flex: 1 }}
          >
            {appName}
          </Link>
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
