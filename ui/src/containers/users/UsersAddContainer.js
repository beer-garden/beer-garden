import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { compose } from "recompose";
import { Redirect, withRouter } from "react-router-dom";
import { withStyles } from "@material-ui/core/styles";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import PersonAdd from "@material-ui/icons/PersonAdd";
import Save from "@material-ui/icons/Save";

import { createUser } from "../../actions/user";
import UsersFormContainer from "./UsersFormContainer";

const styles = theme => ({
  leftIcon: {
    marginRight: theme.spacing.unit,
  },
  rightButton: {
    marginLeft: "auto",
  },
  row: {
    display: "flex",
    flexDirection: "row",
  },
});

export class UsersAddContainer extends Component {
  state = {
    newUsername: "",
    redirect: false,
  };

  saveUser = (username, password, roleNames) => {
    this.props.createUser(username, password, roleNames).then(() => {
      if (!this.props.createUserError) {
        this.setState({ redirect: true, newUsername: username });
      }
    });
  };

  render() {
    const {
      classes,
      currentUser,
      createUserError,
      createUserLoading,
      location,
    } = this.props;

    if (this.state.redirect) {
      const parts = location.pathname.split("/");
      const base = parts.slice(0, parts.length - 1).join("/");
      return <Redirect to={`${base}/${this.state.newUsername}`} />;
    }

    const header = (
      <div className={classes.row}>
        <PersonAdd className={classes.leftIcon} fontSize="large" />
        <Typography variant="h4">New User</Typography>
        <Button
          className={classes.rightButton}
          color="primary"
          disabled={createUserLoading}
          size="large"
          type="submit"
        >
          <Save className={classes.leftIcon} />
          Save
        </Button>
      </div>
    );

    return (
      <UsersFormContainer
        header={header}
        currentUser={currentUser}
        handleSubmit={this.saveUser}
        error={createUserError}
        requirePassword={true}
      />
    );
  }
}

UsersAddContainer.propTypes = {
  classes: PropTypes.object.isRequired,
  currentUser: PropTypes.object.isRequired,
  createUser: PropTypes.func.isRequired,
  createUserLoading: PropTypes.bool.isRequired,
  createUserError: PropTypes.object,
  location: PropTypes.object.isRequired,
};

const mapStateToProps = state => {
  return {
    currentUser: state.authReducer.userData,
    createUserLoading: state.userReducer.createUserLoading,
    createUserError: state.userReducer.createUserError,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    createUser: (username, password, roles) =>
      dispatch(createUser(username, password, roles)),
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

export default enhance(UsersAddContainer);
