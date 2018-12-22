import React, { Component } from "react";
import { connect } from "react-redux";
import { loadConfig } from "../actions/config";
import PropTypes from "prop-types";
import { MuiThemeProvider } from "@material-ui/core";
import { Switch, Route, withRouter } from "react-router-dom";
import Spinner from "../components/layout/Spinner";
import ErrorRetryDialog from "../components/layout/ErrorRetryDialog";
import LoginDashboard from "../containers/auth/LoginDashboard";
import App from "./App";

export class Root extends Component {
  componentDidMount() {
    this.props.loadConfig();
  }

  render() {
    const {
      configLoading,
      configError,
      config,
      loadConfig,
      theme,
    } = this.props;

    let element;
    if (configLoading && configError === null) {
      element = <Spinner />;
    } else if (configError) {
      return (
        <ErrorRetryDialog
          error={configError}
          action={loadConfig}
          loading={configLoading}
        />
      );
    } else {
      document.title = config.applicationName;
      element = (
        <Switch>
          <Route exact path="/" component={App} />
          <Route exact path="/login" component={LoginDashboard} />
        </Switch>
      );
    }

    return <MuiThemeProvider theme={theme}>{element}</MuiThemeProvider>;
  }
}

const mapStateToProps = state => {
  return {
    config: state.configReducer.config,
    configLoading: state.configReducer.configLoading,
    configError: state.configReducer.configError,
    theme: state.themeReducer.theme,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadConfig: () => dispatch(loadConfig()),
  };
};

Root.propTypes = {
  loadConfig: PropTypes.func.isRequired,
  config: PropTypes.object.isRequired,
  configLoading: PropTypes.bool.isRequired,
  configError: PropTypes.object,
  theme: PropTypes.object.isRequired,
};

export default withRouter(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  )(Root),
);
