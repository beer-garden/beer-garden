import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { Redirect, withRouter } from "react-router-dom";
import { setUserTheme } from "../actions/theme";
import { logout } from "../actions/auth";
import Topbar from "../components/layout/Topbar";
import SystemDashboard from "./SystemDashboard";

export class App extends Component {
  render() {
    const { config, auth, themeName, setUserTheme, logout } = this.props;

    if (config.authEnabled && !auth.isAuthenticated) {
      return <Redirect to="/login" />;
    }

    return (
      <div style={{ display: "flex" }}>
        <Topbar
          appName={config.applicationName}
          isAuthenticated={auth.isAuthenticated}
          themeName={themeName}
          setUserTheme={setUserTheme}
          logout={logout}
        />
        <SystemDashboard />
      </div>
    );
  }
}

const mapStateToProps = state => {
  return {
    config: state.configReducer.config,
    auth: state.authReducer,
    themeName: state.themeReducer.themeName,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    setUserTheme: name => dispatch(setUserTheme(name)),
    logout: () => dispatch(logout()),
  };
};

App.propTypes = {
  config: PropTypes.object.isRequired,
  auth: PropTypes.object.isRequired,
  setUserTheme: PropTypes.func.isRequired,
  logout: PropTypes.func.isRequired,
  themeName: PropTypes.string.isRequired,
};

export default withRouter(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  )(App),
);
