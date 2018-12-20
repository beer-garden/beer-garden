import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { Typography, withStyles } from '@material-ui/core';
import Topbar from '../components/layout/Topbar';
import Sidebar from '../components/layout/Sidebar';
import SystemList from '../components/systems/SystemList';

const styles = theme => {
  console.log(theme.mixins.toolbar);
  return {
    root: {
      display: 'flex',
    },
    content: {
      flexGrow: 1,
      padding: theme.spacing.unit * 2,
    },
    topbarSpacer: theme.mixins.toolbar,
  };
};

class Dashboard extends Component {
  systems = [
    { id: 1, name: 'system1', version: '1.0.0' },
    { id: 2, name: 'system2', version: '1.0.0' },
  ];
  render() {
    const { classes, config, auth } = this.props;
    return (
      <div className={classes.root}>
        <Topbar
          appName={config.applicationName}
          isAuthenticated={auth.isAuthenticated}
        />
        <Sidebar />
        <main className={classes.content}>
          <div className={classes.topbarSpacer} />
          <SystemList systems={this.systems} />
        </main>
      </div>
    );
  }
}

Dashboard.propTypes = {
  config: PropTypes.object.isRequired,
  auth: PropTypes.object.isRequired,
  classes: PropTypes.object.isRequired,
};

export default connect(state => ({
  config: state.configReducer.config,
  auth: state.authReducer,
}))(withStyles(styles)(Dashboard));
