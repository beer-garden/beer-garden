import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Redirect } from 'react-router-dom';
import { withStyles } from '@material-ui/core/styles';
import { Grid, Hidden } from '@material-ui/core';
import Topbar from '../../components/layout/Topbar';
import Login from '../../components/auth/Login';
import { basicLogin } from '../../actions/auth';

const styles = theme => ({
  content: {
    flewGrow: 1,
    padding: theme.spacing.unit * 3,
    height: '100vh',
    overflow: 'auto',
  },
  topbarSpacer: theme.mixins.toolbar,
});

export class LoginDashboard extends Component {
  login = formData => {
    const { basicLogin, history } = this.props;
    basicLogin(formData.username, formData.password, formData.rememberMe).then(
      data => {
        console.log('successfully logged in...');
        console.log(data);
        console.log('I should redirect');
        history.push('/');
      },
    );
  };

  guestLogin = formData => {
    const { basicLogin, history } = this.props;
    basicLogin('anonymous', null, formData.rememberMe).then(data => {
      localStorage.setItem('loggedInAsGuest', true);
      history.push('/');
    });
  };

  render() {
    const { classes, config, auth } = this.props;
    if (!config.authEnabled || auth.isAuthenticated) {
      return <Redirect to="/" />;
    }

    return (
      <>
        <Topbar
          appName={config.applicationName}
          isAuthenticated={auth.isAuthenticated}
        />
        <div className={classes.topbarSpacer} />
        <main className={classes.content}>
          <Grid container>
            <Hidden xsDown>
              <Grid item xs />
            </Hidden>
            <Login
              guestLoginEnabled={config.guestLoginEnabled}
              loading={auth.userLoading}
              error={auth.userError}
              login={this.login}
              guestLogin={this.guestLogin}
            />
            <Hidden xsDown>
              <Grid item xs />
            </Hidden>
          </Grid>
        </main>
      </>
    );
  }
}

LoginDashboard.propTypes = {
  classes: PropTypes.object.isRequired,
  config: PropTypes.object.isRequired,
  auth: PropTypes.object.isRequired,
  basicLogin: PropTypes.func.isRequired,
};

const mapStateToProps = state => {
  return {
    config: state.configReducer.config,
    auth: state.authReducer,
  };
};

export default connect(
  mapStateToProps,
  {
    basicLogin: basicLogin,
  },
)(withStyles(styles)(LoginDashboard));
