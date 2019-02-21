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

import PermissionList from "../../components/users/PermissionList";
import {
  hasPermissions,
  coalescePermissions,
  isValidPassword,
  toggleItemInArray,
} from "../../utils";
import { createUser } from "../../actions/user";
import {
  ALL,
  LIST_ALL,
  ROLE_CREATE,
  ROLE_READ,
} from "../../constants/permissions";
import RoleRowContainer from "./RoleRowContainer";
import UserForm from "../../components/users/UserForm";

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
  topPad: {
    paddingTop: theme.spacing.unit,
  },
  error: {
    color: theme.palette.error.dark,
  },
});

export class UsersAddContainer extends Component {
  state = {
    username: {
      value: "",
      error: false,
      help: "",
    },
    password: {
      value: "",
      error: false,
      help: "",
    },
    confirmPassword: {
      value: "",
      error: false,
      help: "",
    },
    permissions: { value: [], error: false, help: "" },
    newRoleName: {
      value: "",
      error: false,
      help: "",
    },
    newRoleDescription: {
      value: "",
      error: false,
      help: "",
    },
    newRolePermissions: {
      value: [],
      error: false,
      help: "",
    },
    selectedRoles: [],
    savingUser: false,
    redirect: false,
    triggerRoleSave: false,
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
    if (!this.validateUser()) {
      return;
    }
    this.saveUser();
  };

  afterSaveRole = role => {
    if (this.state.triggerRoleSave) {
      this.setState({ triggerRoleSave: false });
    }

    this.handleRoleSelect(role);

    if (this.state.savingUser) {
      this.saveUser();
    }
  };

  saveUser = () => {
    this.setState({ savingUser: true });

    const { permissions, username, password, selectedRoles } = this.state;
    const { createUser } = this.props;

    // If there are any permissions which do not belong to a role, then
    // we have to save a role first.
    if (permissions.value.find(p => !p.inherited)) {
      this.setState({ triggerRoleSave: true });
      return;
    }

    createUser(
      username.value,
      password.value,
      selectedRoles.map(r => r.name),
    ).then(() => {
      if (!this.props.createUserError) {
        this.setState({ redirect: true, savingUser: false });
      }
    });
  };

  validateRole = () => {
    const { newRoleName, newRolePermissions } = this.state;

    let valid = true;
    if (!newRoleName.value) {
      valid = false;
      this.setState({
        newRoleName: {
          value: newRoleName.value,
          error: true,
          help: "Role name is required",
        },
      });
    }

    if (newRolePermissions.value.length === 0) {
      valid = false;
      this.setState({
        newRolePermissions: {
          value: newRolePermissions.value,
          error: true,
          help: "Please select at least one permission",
        },
      });
    }

    return valid;
  };

  validateUser = () => {
    const { username, password, confirmPassword, permissions } = this.state;
    const { currentUser } = this.props;
    const newUsername = { value: username.value, error: false, help: "" };
    const newPassword = { value: password.value, error: false, help: "" };
    const newConfirmPassword = {
      value: confirmPassword.value,
      error: false,
      help: "",
    };
    const newPerms = { value: permissions.value, error: false, help: "" };

    if (!newUsername.value) {
      newUsername.error = true;
      newUsername.help = "Username is required";
    }

    if (!newPassword.value) {
      newPassword.error = true;
      newPassword.help = "Password is required";
    }

    if (!newConfirmPassword.value) {
      newConfirmPassword.error = true;
      newConfirmPassword.help = "Confirmation password is required";
    }

    if (permissions.value.length === 0) {
      newPerms.error = true;
      let message;
      if (hasPermissions(currentUser, [ROLE_CREATE, ROLE_READ])) {
        message =
          "No permissions, either select permissions below, or select an already created role";
      } else if (hasPermissions(currentUser, [ROLE_READ])) {
        message = "No permissions, select an already created role";
      } else {
        message = "No permissions, select from permissions below";
      }
      newPerms.help = message;
    }

    if (
      newUsername.error ||
      newPassword.error ||
      newConfirmPassword.error ||
      newPerms.error
    ) {
      this.setState({
        username: newUsername,
        password: newPassword,
        confirmPassword: newConfirmPassword,
        permissions: newPerms,
      });
      return false;
    }

    if (password.value !== confirmPassword.value) {
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

  // This method exist because rendering the PermissionList is expensive
  // and using arrow functions means that they re-render needlessly.
  toggleAndUpdatePermission = event => {
    this.togglePermission(event, true);
  };

  // This method exist because rendering the PermissionList is expensive
  // and using arrow functions means that they re-render needlessly.
  toggleNewPermission = event => {
    this.togglePermission(event, false);
  };

  togglePermission = (event, updateUserRoles) => {
    const { permissions, newRolePermissions } = this.state;
    const {
      target: { value },
    } = event;

    const key = "value";
    const formatter = v => ({ value: v, inherited: false });

    if (updateUserRoles) {
      this.setState({
        permissions: {
          value: toggleItemInArray(permissions.value, value, key, formatter),
          error: false,
          help: "",
        },
      });
    }

    this.setState({
      newRolePermissions: {
        value: toggleItemInArray(
          newRolePermissions.value,
          value,
          key,
          formatter,
        ),
        error: false,
        help: "",
      },
    });
  };

  handleRoleSelect = role => {
    const { selectedRoles } = this.state;
    const newRoles = toggleItemInArray(
      selectedRoles,
      role,
      "name",
      null,
      "name",
    );

    const { permissions } = coalescePermissions(newRoles);
    this.updateInheritedPermissions(permissions);
    this.setState({ selectedRoles: newRoles });
  };

  updateInheritedPermissions = perms => {
    const inheritedPerms = perms.has(ALL) ? new Set(LIST_ALL) : perms;
    const newPerms = [];
    const newRolePerms = [];

    // On current permissions, only keep the ones that are either
    // inherited and in the new list of inherited permissions or
    // not inherited. Un-inherited permissions are only added to
    // the newRolePerms
    this.state.permissions.value.forEach(perm => {
      if (perm.inherited && inheritedPerms.has(perm.value)) {
        newPerms.push(perm);
      } else if (!perm.inherited) {
        newPerms.push(perm);
        newRolePerms.push(perm);
      }
    });

    inheritedPerms.forEach(perm => {
      const foundPerm = newPerms.find(p => p.value === perm);
      if (foundPerm) {
        foundPerm.inherited = true;
      } else {
        newPerms.push({ value: perm, inherited: true });
      }

      const rolePermIndex = newRolePerms.findIndex(p => p.value === perm);
      if (rolePermIndex !== -1) {
        newRolePerms.splice(rolePermIndex, 1);
      }
    });

    this.setState({
      permissions: { value: newPerms, error: false, help: "" },
      newRolePermissions: { value: newRolePerms, error: false, help: "" },
    });
  };

  renderRoleRow = () => {
    const { currentUser } = this.props;
    const {
      newRolePermissions,
      newRoleName,
      newRoleDescription,
      selectedRoles,
      triggerRoleSave,
    } = this.state;

    if (!hasPermissions(currentUser, [ROLE_READ])) {
      return null;
    }

    return (
      <RoleRowContainer
        afterSaveRole={this.afterSaveRole}
        selectedRoles={selectedRoles}
        handleRoleClick={this.handleRoleSelect}
        handleFormChange={this.handleFormChange}
        permissions={newRolePermissions}
        newRoleDescription={newRoleDescription}
        newRoleName={newRoleName}
        togglePermission={this.toggleNewPermission}
        triggerRoleSave={triggerRoleSave}
        validateRole={this.validateRole}
      />
    );
  };

  render() {
    const {
      classes,
      currentUser,
      createUserError,
      createUserLoading,
    } = this.props;
    const { username, password, confirmPassword, permissions } = this.state;

    if (this.state.redirect) {
      //TODO: Use relative path somehow
      return <Redirect to={`/advanced/users/${this.state.username.value}`} />;
    }

    return (
      <form onSubmit={this.handleSubmit}>
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
        <Typography align="right" variant="body1" className={classes.error}>
          {createUserError && createUserError.message}
        </Typography>
        <UserForm
          handleFormChange={this.handleFormChange}
          username={username}
          password={password}
          confirmPassword={confirmPassword}
        />
        {this.renderRoleRow()}
        <div className={classes.topPad}>
          <Typography color="error">{permissions.help}</Typography>
          <PermissionList
            edit={hasPermissions(currentUser, [ROLE_CREATE])}
            togglePermission={this.toggleAndUpdatePermission}
            permissions={permissions.value}
          />
        </div>
      </form>
    );
  }
}

UsersAddContainer.propTypes = {
  classes: PropTypes.object.isRequired,
  currentUser: PropTypes.object.isRequired,
  createUser: PropTypes.func.isRequired,
  createUserLoading: PropTypes.bool.isRequired,
  createUserError: PropTypes.object,
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
