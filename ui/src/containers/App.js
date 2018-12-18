import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Link, Route, Redirect, withRouter } from 'react-router-dom';
import Dashboard from '../components/example/Dashboard';

export class App extends Component {
  render() {
    const { config, auth } = this.props;

    if (config.authEnabled && !auth.isAuthenticated) {
      return <Redirect to="/login" />;
    }

    return <Dashboard />;
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
