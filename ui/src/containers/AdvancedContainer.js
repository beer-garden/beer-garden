import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { compose } from "recompose";
import { Switch, withRouter } from "react-router-dom";
import { withStyles } from "@material-ui/core";
import AuthRoute from "./auth/AuthRoute";
import AdvancedIndex from "../components/advanced/index";
import AboutContainer from "./advanced/AboutContainer";
import SystemsContainer from "./advanced/SystemsContainer";
import QueuesContainer from "./advanced/QueuesContainer";
import UsersContainer from "./advanced/UsersContainer";

const styles = theme => ({
  root: {
    width: "100%",
    backgroundColor: theme.palette.background.paper,
  },
});

export class AdvancedContainer extends Component {
  render() {
    const { classes, match, authEnabled, userData } = this.props;
    return (
      <div className={classes.root}>
        <Switch>
          <AuthRoute
            exact
            path={`${match.path}/`}
            render={props => (
              <AdvancedIndex
                {...props}
                authEnabled={authEnabled}
                userData={userData}
              />
            )}
          />
          <AuthRoute
            exact
            path={`${match.path}/about`}
            component={AboutContainer}
          />
          <AuthRoute
            exact
            path={`${match.path}/systems`}
            component={SystemsContainer}
          />
          <AuthRoute
            exact
            path={`${match.path}/queues`}
            component={QueuesContainer}
          />
          <AuthRoute
            exact
            path={`${match.path}/users`}
            component={UsersContainer}
          />
        </Switch>
      </div>
    );
  }
}

AdvancedContainer.propTypes = {
  authEnabled: PropTypes.bool.isRequired,
  userData: PropTypes.object.isRequired,
  classes: PropTypes.object.isRequired,
  match: PropTypes.object.isRequired,
};

const mapStateToProps = state => ({
  authEnabled: state.configReducer.config.authEnabled,
  userData: state.authReducer.userData,
});

const enhanced = compose(
  connect(mapStateToProps),
  withStyles(styles),
  withRouter,
);

export default enhanced(AdvancedContainer);
