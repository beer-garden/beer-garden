import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { Switch, Route, Redirect, withRouter } from "react-router-dom";
import { setUserTheme } from "../actions/theme";
import { logout } from "../actions/auth";
import SystemsContainer from "./SystemsContainer";
import CommandsContainer from "./CommandsContainer";
import RequestsContainer from "./RequestsContainer";
import SchedulerContainer from "./SchedulerContainer";
import AdvancedContainer from "./AdvancedContainer";
import Layout from "../components/layout";

export class App extends Component {
  render() {
    const { config, auth, themeName, setUserTheme, logout } = this.props;

    if (config.authEnabled && !auth.isAuthenticated) {
      return <Redirect to="/login" />;
    }

    return (
      <Layout
        appName={config.applicationName}
        themeName={themeName}
        setUserTheme={setUserTheme}
        logout={logout}
        isAuthenticated={auth.isAuthenticated}
      >
        <Switch>
          <Route exact path="/" component={SystemsContainer} />
          <Route exact path="/commands" component={CommandsContainer} />
          <Route exact path="/requests" component={RequestsContainer} />
          <Route exact path="/scheduler" component={SchedulerContainer} />
          <Route exact path="/advanced" component={AdvancedContainer} />
        </Switch>
      </Layout>
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
