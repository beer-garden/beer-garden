import React, { Component } from "react";
import PropTypes from "prop-types";
import { withStyles } from "@material-ui/core";
import Topbar from "./Topbar";
import Sidebar from "./Sidebar";

const styles = theme => ({
  root: {
    display: "flex",
  },
  content: {
    flexGrow: 1,
    padding: theme.spacing.unit * 2,
    backgroundColor: theme.palette.background.default,
    height: "100vh",
  },
  topbarSpacer: theme.mixins.toolbar,
});

export class Layout extends Component {
  state = {
    mobileOpen: false,
  };

  handleDrawerToggle = () => {
    this.setState({ mobileOpen: !this.state.mobileOpen });
  };

  render() {
    const {
      classes,
      children,
      appName,
      isAuthenticated,
      authEnabled,
      themeName,
      setUserTheme,
      logout,
    } = this.props;
    const { mobileOpen } = this.state;

    const sidebar =
      !authEnabled || isAuthenticated ? (
        <Sidebar
          mobileOpen={mobileOpen}
          toggleDrawer={this.handleDrawerToggle}
        />
      ) : null;

    return (
      <div className={classes.root}>
        <Topbar
          appName={appName}
          isAuthenticated={isAuthenticated}
          authEnabled={authEnabled}
          themeName={themeName}
          setUserTheme={setUserTheme}
          logout={logout}
          toggleDrawer={this.handleDrawerToggle}
        />
        {sidebar}
        <main className={classes.content}>
          <div className={classes.topbarSpacer} />
          {children}
        </main>
      </div>
    );
  }
}

Layout.propTypes = {
  classes: PropTypes.object.isRequired,
  appName: PropTypes.string.isRequired,
  themeName: PropTypes.string.isRequired,
  setUserTheme: PropTypes.func.isRequired,
  logout: PropTypes.func.isRequired,
  isAuthenticated: PropTypes.bool.isRequired,
  authEnabled: PropTypes.bool.isRequired,
};

export default withStyles(styles)(Layout);
