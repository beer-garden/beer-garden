import React, { Component } from 'react';
import { connect } from 'react-redux';
import { loadConfig } from '../actions/config';
import PropTypes from 'prop-types';
import { Switch, Route, withRouter } from 'react-router-dom';
import Spinner from '../components/layout/Spinner';
import ErrorRetryDialog from '../components/layout/ErrorRetryDialog';
import App from './App';

export class Root extends Component {
  componentDidMount() {
    this.props.loadConfig();
  }

  render() {
    const { configLoading, configError, config, loadConfig } = this.props;

    if (configLoading && configError === null) {
      return <Spinner />;
    }

    if (configError) {
      return (
        <ErrorRetryDialog
          error={configError}
          action={loadConfig}
          loading={configLoading}
        />
      );
    }

    document.title = config.applicationName;
    return (
      <Switch>
        <Route exact path="/" component={App} />
      </Switch>
    );
  }
}

const mapStateToProps = state => {
  return {
    config: state.configReducer.config,
    configLoading: state.configReducer.configLoading,
    configError: state.configReducer.configError,
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
};

export default withRouter(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  )(Root),
);
