import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { withStyles } from "@material-ui/core/styles";
import { Switch, withRouter } from "react-router-dom";
import Paper from "@material-ui/core/Paper";
import AuthRoute from "../auth/AuthRoute";
import UsersAddContainer from "./UsersAddContainer";
import UsersListContainer from "./UsersListContainer";
import UsersViewContainer from "./UsersViewContainer";

const styles = theme => ({
  root: {
    ...theme.mixins.gutters(),
    paddingTop: theme.spacing.unit * 2,
    paddingBottom: theme.spacing.unit * 2,
  },
});

export class UsersRoot extends Component {
  render() {
    const { classes, match } = this.props;
    return (
      <Paper className={classes.root}>
        <Switch>
          <AuthRoute
            exact
            path={`${match.path}/`}
            component={UsersListContainer}
          />
          <AuthRoute
            exact
            path={`${match.path}/add`}
            component={UsersAddContainer}
          />
          <AuthRoute
            exact
            path={`${match.path}/:username`}
            component={UsersViewContainer}
          />
        </Switch>
      </Paper>
    );
  }
}

UsersRoot.propTypes = {
  match: PropTypes.object.isRequired,
};

const enhanced = compose(
  withRouter,
  withStyles(styles),
);

export default enhanced(UsersRoot);
