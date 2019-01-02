import React, { Component } from "react";
import { compose } from "recompose";
import { connect } from "react-redux";
import { loadConfig } from "../actions/config";
import { loadUserData } from "../actions/auth";
import PropTypes from "prop-types";
import { MuiThemeProvider } from "@material-ui/core";
import { withRouter } from "react-router-dom";
import Spinner from "../components/layout/Spinner";
import ErrorRetryDialog from "../components/layout/ErrorRetryDialog";
import App from "./App";

export class Root extends Component {
  componentDidMount() {
    const { loadConfig } = this.props;

    loadConfig().then(() => {
      const { config, userData, isAuthenticated, loadUserData } = this.props;
      if (!config.authEnabled) {
        return;
      }

      if (isAuthenticated && Object.keys(userData).length === 0) {
        loadUserData();
      }
    });
  }

  render() {
    const {
      userLoading,
      configLoading,
      configError,
      config,
      loadConfig,
      theme,
    } = this.props;

    if (configError) {
      return (
        <ErrorRetryDialog
          error={configError}
          action={loadConfig}
          loading={configLoading}
        />
      );
    }

    let element;
    if (configLoading || userLoading) {
      element = <Spinner />;
    } else {
      document.title = config.applicationName;
      element = <App />;
    }

    return <MuiThemeProvider theme={theme}>{element}</MuiThemeProvider>;
  }
}

const mapStateToProps = state => {
  return {
    isAuthenticated: state.authReducer.isAuthenticated,
    userLoading: state.authReducer.userLoading,
    userData: state.authReducer.userData,
    config: state.configReducer.config,
    configLoading: state.configReducer.configLoading,
    configError: state.configReducer.configError,
    theme: state.themeReducer.theme,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadConfig: () => dispatch(loadConfig()),
    loadUserData: () => dispatch(loadUserData()),
  };
};

Root.propTypes = {
  loadConfig: PropTypes.func.isRequired,
  config: PropTypes.object.isRequired,
  configLoading: PropTypes.bool.isRequired,
  configError: PropTypes.object,
  theme: PropTypes.object.isRequired,
};

const enhance = compose(
  withRouter,
  connect(
    mapStateToProps,
    mapDispatchToProps,
  ),
);

export default enhance(Root);
