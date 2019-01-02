import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { Redirect, withRouter } from "react-router-dom";
import { withStyles } from "@material-ui/core/styles";
import { Grid, Hidden } from "@material-ui/core";
import Topbar from "../../components/layout/Topbar";
import Login from "../../components/auth/Login";
import { basicLogin } from "../../actions/auth";
import { compose } from "recompose";

const styles = theme => ({
  content: {
    flewGrow: 1,
    padding: theme.spacing.unit * 3,
    height: "100vh",
    overflow: "auto",
    backgroundColor: theme.palette.background.default,
  },
  topbarSpacer: theme.mixins.toolbar,
});

export class LoginDashboard extends Component {
  login = formData => {
    const { basicLogin } = this.props;
    basicLogin(formData.username, formData.password, formData.rememberMe);
  };

  guestLogin = formData => {
    const { basicLogin } = this.props;
    basicLogin("anonymous", null, formData.rememberMe);
  };

  render() {
    const { classes, config, auth } = this.props;
    if (!config.authEnabled || auth.isAuthenticated) {
      const { from } = this.props.location.state || { from: { pathname: "/" } };
      return <Redirect to={from} />;
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

const mapDispatchToProps = dispatch => {
  return {
    basicLogin: (username, password) =>
      dispatch(basicLogin(username, password)),
  };
};

const enhance = compose(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  ),
  withStyles(styles),
  withRouter,
);
export default enhance(LoginDashboard);
