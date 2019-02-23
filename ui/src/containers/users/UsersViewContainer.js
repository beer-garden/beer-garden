import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { connect } from "react-redux";
import { Redirect, withRouter } from "react-router-dom";
import Typography from "@material-ui/core/Typography";
import isEqual from "lodash.isequal";

import { getUser, deleteUser, updateUser } from "../../actions/user";
import Spinner from "../../components/layout/Spinner";
import { hasPermissions } from "../../utils";
import UserInfo from "../../components/users/UserInfo";
import UserInfoHeader from "../../components/users/UserInfoHeader";
import { USER_DELETE, USER_UPDATE } from "../../constants/permissions";
import UsersFormContainer from "./UsersFormContainer";

export class UsersViewContainer extends Component {
  state = {
    editing: false,
    redirect: false,
  };

  componentDidMount() {
    const { match, getUser } = this.props;
    getUser(match.params.username);
  }

  deleteUser = () => {
    const { selectedUser, deleteUser } = this.props;
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
        onDelete={this.deleteUser}
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
