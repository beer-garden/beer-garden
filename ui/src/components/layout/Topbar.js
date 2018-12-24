import React, { Component } from "react";
import PropTypes from "prop-types";
import { withStyles } from "@material-ui/core/styles";
import { AppBar, Toolbar, Typography } from "@material-ui/core";
import UserIcon from "./UserIcon";

const styles = theme => ({
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
  },
});

export class Topbar extends Component {
  state = {
    anchorEl: null,
  };

  handleMenu = event => {
    this.setState({ anchorEl: event.currentTarget });
  };

  handleClose = event => {
    this.setState({ anchorEl: null });
  };

  render() {
    const {
      classes,
      appName,
      isAuthenticated,
      setUserTheme,
      themeName,
      logout,
    } = this.props;

    return (
      <AppBar position="fixed" color="primary" className={classes.appBar}>
        <Toolbar>
          <Typography variant="h6" color="inherit" style={{ flex: 1 }}>
            {appName}
          </Typography>
          {isAuthenticated ? (
            <UserIcon
              themeName={themeName}
              setUserTheme={setUserTheme}
              logout={logout}
            />
          ) : null}
        </Toolbar>
      </AppBar>
    );
  }
}

Topbar.propTypes = {
  appName: PropTypes.string.isRequired,
  isAuthenticated: PropTypes.bool.isRequired,
  classes: PropTypes.object.isRequired,
  themeName: PropTypes.string,
  setUserTheme: PropTypes.func,
  logout: PropTypes.func,
};

export default withStyles(styles)(Topbar);
