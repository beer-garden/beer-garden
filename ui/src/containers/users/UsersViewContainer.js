import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { connect } from "react-redux";
import { Redirect, withRouter } from "react-router-dom";
import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
import Typography from "@material-ui/core/Typography";
import isEqual from "lodash.isequal";

import { getUser, deleteUser, updateUser } from "../../actions/user";
import Spinner from "../../components/layout/Spinner";
import { hasPermissions } from "../../utils";
import UserInfo from "../../components/users/UserInfo";
import UserInfoHeader from "../../components/users/UserInfoHeader";
import { PROTECTED_USERS } from "../../constants/auth";
import { USER_DELETE, USER_UPDATE } from "../../constants/permissions";
import UsersFormContainer from "./UsersFormContainer";

export class UsersViewContainer extends Component {
  state = {
    editing: false,
    redirect: false,
    confirmAction: false,
    showConfirmDialog: false,
    confirmDialogText: "",
  };

  componentDidMount() {
    const { match, getUser } = this.props;
    getUser(match.params.username);
  }

  deleteUserDialog = () => {
    const { selectedUser, currentUser } = this.props;

    if (PROTECTED_USERS.indexOf(selectedUser.username) !== -1) {
      this.setState({
        showConfirmDialog: true,
        confirmDialogText:
          "You are about to delete a protected user, this often means that " +
          "you will need to have modified configurations. Delete this user?",
      });
    } else if (selectedUser.username === currentUser.username) {
      this.setState({
        showConfirmDialog: true,
        confirmDialogText:
          "You are about to delete the current user. This will automatically " +
          "log you out. Delete this user?",
      });
    } else {
      this.deleteUser();
    }
  };

  deleteUser = () => {
    const { selectedUser, deleteUser } = this.props;
    this.handleClose();
    deleteUser(selectedUser.id).then(() => {
      if (!this.props.deleteUserError) {
        this.setState({ redirect: true });
      }
    });
  };

  handleUpdate = (newUsername, newPassword, newRoles) => {
    const { selectedUser, updateUser } = this.props;
    const roleNames = selectedUser.roles.map(r => r.name);
    if (
      newUsername !== selectedUser.username ||
      newPassword ||
      !isEqual(newRoles, roleNames)
    ) {
      updateUser(
        {
          id: selectedUser.id,
          username: selectedUser.username,
          roles: selectedUser.roles.map(r => r.name),
        },
        {
          username: newUsername,
          password: newPassword,
          roles: newRoles,
        },
      ).then(() => {
        if (!this.props.updateUserError) {
          this.toggleEdit();
        }
      });
    } else {
      this.toggleEdit();
    }
  };

  toggleEdit = () => {
    this.setState({ editing: !this.state.editing });
  };

  handleClose = () => {
    this.setState({ showConfirmDialog: false });
  };

  renderDialog = () => {
    return (
      <Dialog
        open={this.state.showConfirmDialog}
        onClose={this.handleClose}
        aria-describedby="alert-dialog-description"
      >
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            {this.state.confirmDialogText}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={this.handleClose} color="primary">
            Cancel
          </Button>
          <Button onClick={this.deleteUser} color="primary" autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  render() {
    const {
      userLoading,
      userError,
      currentUser,
      location,
      deleteUserLoading,
      deleteUserError,
      updateUserError,
      updateUserLoading,
      selectedUser,
    } = this.props;
    const { redirect, editing } = this.state;

    if (redirect) {
      const parts = location.pathname.split("/");
      const to = parts.slice(0, parts.length - 1).join("/");
      return <Redirect to={to} />;
    } else if (userLoading) {
      return <Spinner />;
    } else if (userError) {
      return <Typography>TODO: Render an error</Typography>;
    }

    const header = (
      <UserInfoHeader
        canEdit={hasPermissions(currentUser, [USER_UPDATE])}
        canDelete={hasPermissions(currentUser, [USER_DELETE])}
        editing={editing}
        onCancelEdit={this.toggleEdit}
        onEdit={this.toggleEdit}
        onDelete={this.deleteUserDialog}
        deleting={deleteUserLoading}
        errorMessage={deleteUserError ? deleteUserError.message : ""}
        saving={updateUserLoading}
      />
    );

    if (editing) {
      return (
        <UsersFormContainer
          error={updateUserError}
          handleSubmit={this.handleUpdate}
          permissions={selectedUser.permissions}
          selectedRoles={selectedUser.roles}
          username={selectedUser.username}
          header={header}
          requirePassword={false}
        />
      );
    } else {
      return (
        <>
          {header}
          <UserInfo user={selectedUser} />
          {this.renderDialog()}
        </>
      );
    }
  }
}

UsersViewContainer.propTypes = {
  currentUser: PropTypes.object.isRequired,
  selectedUser: PropTypes.object.isRequired,
  userLoading: PropTypes.bool.isRequired,
  userError: PropTypes.object,
  deleteUserError: PropTypes.object,
  deleteUserLoading: PropTypes.bool.isRequired,
  updateUserError: PropTypes.object,
  updateUserLoading: PropTypes.bool.isRequired,
  updateUser: PropTypes.func.isRequired,
};

const mapStateToProps = state => {
  return {
    currentUser: state.authReducer.userData,
    selectedUser: state.userReducer.selectedUser,
    userLoading: state.userReducer.userLoading,
    userError: state.userReducer.userError,
    deleteUserError: state.userReducer.deleteUserError,
    deleteUserLoading: state.userReducer.deleteUserLoading,
    updateUserError: state.userReducer.updateUserError,
    updateUserLoading: state.userReducer.updateUserLoading,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    getUser: username => dispatch(getUser(username)),
    deleteUser: id => dispatch(deleteUser(id)),
    updateUser: (currentUser, newUser) =>
      dispatch(updateUser(currentUser, newUser)),
  };
};

const enhance = compose(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  ),
  withRouter,
);

export default enhance(UsersViewContainer);
