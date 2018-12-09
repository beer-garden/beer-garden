import React, { Component } from 'react';
import { connect } from 'react-redux';
import { loadConfig } from '../actions/config';
import CssBaseline from '@material-ui/core/CssBaseline';
import PropTypes from 'prop-types';
import { Route } from 'react-router-dom';
import Spinner from '../components/layout/Spinner';
import ErrorRetryDialog from '../components/layout/ErrorRetryDialog';
import App from './App';
import Login from '../components/auth/Login';

export class Root extends Component {
  componentDidMount() {
    this.props.loadConfig();
  }

  render() {
    const { configLoading, configError, config, loadConfig } = this.props;

    if (configLoading && !configError) {
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

    if (config.authEnabled) {
      return <Login />;
    } else {
      return (
        <div>
          <CssBaseline />
          <Route exact path="/" component={App} />
        </div>
      );
    }
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

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Root);
