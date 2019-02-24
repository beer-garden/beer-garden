import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { Redirect } from "react-router-dom";
import { compose } from "recompose";
import { withStyles } from "@material-ui/core/styles";
import Button from "@material-ui/core/Button";
import Paper from "@material-ui/core/Paper";
import Typography from "@material-ui/core/Typography";
import Save from "@material-ui/icons/Save";
import Security from "@material-ui/icons/Security";

import { isValidPassword } from "../../utils";
import UserForm from "../../components/users/UserForm";
import { updateUser } from "../../actions/user";

const styles = theme => ({
  root: {
    ...theme.mixins.gutters(),
    paddingTop: theme.spacing.unit * 2,
    paddingBottom: theme.spacing.unit * 2,
  },
  leftIcon: { marginRight: theme.spacing.unit },
  row: {
    display: "flex",
    flexDirection: "row",
  },
  rightButton: {
    marginLeft: "auto",
  },
  topPad: {
    paddingTop: theme.spacing.unit,
  },
  error: {
    color: theme.palette.error.dark,
  },
});

export class UserSettingsContainer extends Component {
  state = {
    currentPassword: {
      value: "",
      error: false,
      help: "",
    },
    password: {
      value: "",
      error: false,
      help: "",
      label: "New Password",
    },
    confirmPassword: {
      value: "",
      error: false,
      help: "",
      label: "Confirm New Password",
    },
    successMessage: "",
    redirect: false,
  };

  handleFormChange = event => {
    this.setState({
      [event.target.name]: {
        value: event.target.value,
        error: false,
        help: "",
      },
    });
  };

  handleSubmit = e => {
    e.preventDefault();
    if (!this.validatePassword()) {
      return;
    }
    const { currentUser, updateUser, pwChangeRequired } = this.props;
    const { password, currentPassword } = this.state;

    const prevUser = {
      username: currentUser.username,
      id: currentUser.sub,
    };
    const newUser = {
      username: currentUser.username,
      password: password.value,
      currentPassword: currentPassword.value,
    };

    updateUser(prevUser, newUser).then(() => {
      if (!this.props.updateUserError) {
        // It is important that we do not access this variable through
        // the props, instead using the scope above. If we access through
        // the props, the answer will always be false.
        if (pwChangeRequired) {
          this.setState({ redirect: true });
        } else {
          this.setState({ successMessage: "Successfully updated password" });
        }
      }
    });
  };

  validatePassword = () => {
    const { password, confirmPassword, currentPassword } = this.state;
    const newPassword = { value: password.value, error: false, help: "" };
    const newConfirmPassword = {
      value: confirmPassword.value,
      error: false,
      help: "",
    };
    const newCurrentPassword = {
      value: currentPassword.value,
      error: false,
      help: "",
    };

    if (!newPassword.value) {
      newPassword.error = true;
      newPassword.help = "Password is required";
    }

    if (!newConfirmPassword.value) {
      newConfirmPassword.error = true;
      newConfirmPassword.help = "Confirmation password is required";
    }

    if (!newCurrentPassword.value) {
      newCurrentPassword.error = true;
      newCurrentPassword.help = "Current password is required";
    }

    if (
      newPassword.error ||
      newConfirmPassword.error ||
      newCurrentPassword.error
    ) {
      this.setState({
        password: newPassword,
        confirmPassword: newConfirmPassword,
        currentPassword: newCurrentPassword,
      });
      return false;
    }

    if (newPassword.value !== newConfirmPassword.value) {
      newPassword.error = true;
      newPassword.help = "Passwords do not match";
      newConfirmPassword.error = true;
      newConfirmPassword.help = "Passwords do not match";
      this.setState({
        password: newPassword,
        confirmPassword: newConfirmPassword,
      });
      return false;
    }

    const { valid, message } = isValidPassword(password.value);

    if (!valid) {
      newPassword.error = true;
      newPassword.help = message;
      newConfirmPassword.error = true;
      newConfirmPassword.help = message;
      this.setState({
        password: newPassword,
        confirmPassword: newConfirmPassword,
      });
      return false;
    }

    return true;
  };

  render() {
    const {
      classes,
      updateUserError,
      updateUserLoading,
      pwChangeRequired,
    } = this.props;
    const {
      password,
      confirmPassword,
      currentPassword,
      successMessage,
      redirect,
    } = this.state;

    if (redirect) {
      return <Redirect to="/" />;
    }

    return (
      <Paper className={classes.root}>
        <form onSubmit={this.handleSubmit}>
          <div className={classes.row}>
            <Security className={classes.leftIcon} fontSize="large" />
            <Typography variant="h4">Change Password</Typography>

            <Button
              className={classes.rightButton}
              color="primary"
              disabled={updateUserLoading}
              size="large"
              type="submit"
            >
              <Save className={classes.leftIcon} />
              Save
            </Button>
          </div>
          {pwChangeRequired && (
            <Typography variant="body1" gutterBottom>
              You are required to change your password upon initial login.
            </Typography>
          )}
          <Typography align="right" variant="body1" className={classes.error}>
            {updateUserError && updateUserError.message}
          </Typography>
          <Typography align="right" variant="body1">
            {successMessage}
          </Typography>
          <UserForm
            handleFormChange={this.handleFormChange}
            password={password}
            confirmPassword={confirmPassword}
            currentPassword={currentPassword}
          />
        </form>
      </Paper>
    );
  }
}

UserSettingsContainer.propTypes = {
  classes: PropTypes.object.isRequired,
  currentUser: PropTypes.object.isRequired,
  updateUserError: PropTypes.object,
  updateUserLoading: PropTypes.bool.isRequired,
  updateUser: PropTypes.func.isRequired,
  pwChangeRequired: PropTypes.bool.isRequired,
};

const mapStateToProps = state => {
  return {
    currentUser: state.authReducer.userData,
    pwChangeRequired: state.authReducer.pwChangeRequired,
    updateUserLoading: state.userReducer.updateUserLoading,
    updateUserError: state.userReducer.updateUserError,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    updateUser: (prevUser, newUser) => dispatch(updateUser(prevUser, newUser)),
  };
};

const enhance = compose(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  ),
  withStyles(styles),
);

export default enhance(UserSettingsContainer);
