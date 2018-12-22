import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { Link, Route, Redirect, withRouter } from "react-router-dom";
import Topbar from "../components/layout/Topbar";
import Dashboard from "./Dashboard";

export class App extends Component {
  render() {
    const { config, auth } = this.props;

    if (config.authEnabled && !auth.isAuthenticated) {
      return <Redirect to="/login" />;
    }

    return (
      <div style={{ display: "flex" }}>
        <Topbar
          appName={config.applicationName}
          isAuthenticated={auth.isAuthenticated}
        />
        <Dashboard />
      </div>
    );
  }
}

const mapStateToProps = state => {
  return {
    config: state.configReducer.config,
    auth: state.authReducer,
  };
};

const mapDispatchToProps = dispatch => {
  return {};
};

App.propTypes = {
  config: PropTypes.object.isRequired,
  auth: PropTypes.object.isRequired,
};

export default withRouter(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  )(App),
);
