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

import { getRole, deleteRole, updateRole } from "../../actions/role";
import Spinner from "../../components/layout/Spinner";
import { hasPermissions, isEmpty } from "../../utils";
import RoleInfo from "../../components/roles/RoleInfo";
import RoleInfoHeader from "../../components/roles/RoleInfoHeader";
import { ROLE_UPDATE, ROLE_DELETE } from "../../constants/permissions";
import { PROTECTED_ROLES } from "../../constants/auth";

export class RolesViewContainer extends Component {
  state = {
    editing: false,
    redirect: false,
    confirmAction: false,
    showConfirmDialog: false,
    confirmDialogText: "",
  };

  componentDidMount() {
    const { match, getRole } = this.props;
    getRole(match.params.name);
  }

  deleteRoleDialog = () => {
    const { selectedRole, currentUser } = this.props;

    if (PROTECTED_ROLES.indexOf(selectedRole.name) !== -1) {
      this.setState({
        showConfirmDialog: true,
        confirmDialogText:
          "You are about to delete a protected role. Often you" +
          "will need to have modified configurations for this to work. Delete this role?",
      });
    } else if (currentUser.roles.indexOf(selectedRole.name) !== -1) {
      this.setState({
        showConfirmDialog: true,
        confirmDialogText:
          "You are about to delete a role that is active on the current user. " +
          "Delete this role?",
      });
    } else {
      this.deleteRole();
    }
  };

  deleteRole = () => {
    const { selectedRole, deleteRole } = this.props;
    this.handleClose();
    deleteRole(selectedRole.id).then(() => {
      if (!this.props.deleteRoleError) {
        this.setState({ redirect: true });
      }
    });
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
      roleLoading,
      roleError,
      currentUser,
      location,
      deleteRoleLoading,
      deleteRoleError,
      updateRoleLoading,
      selectedRole,
    } = this.props;
    const { redirect, editing } = this.state;

    if (redirect) {
      const parts = location.pathname.split("/");
      const to = parts.slice(0, parts.length - 1).join("/");
      return <Redirect to={to} />;
    } else if (roleError) {
      return <Typography>TODO: Render an error</Typography>;
    } else if (roleLoading || isEmpty(selectedRole)) {
      return <Spinner />;
    }

    const header = (
      <RoleInfoHeader
        canEdit={hasPermissions(currentUser, [ROLE_UPDATE])}
        canDelete={hasPermissions(currentUser, [ROLE_DELETE])}
        editing={editing}
        onCancelEdit={this.toggleEdit}
        onEdit={this.toggleEdit}
        onDelete={this.deleteRoleDialog}
        deleting={deleteRoleLoading}
        errorMessage={deleteRoleError ? deleteRoleError.message : ""}
        saving={updateRoleLoading}
      />
    );

    return (
      <>
        {header}
        <RoleInfo role={selectedRole} />
        {this.renderDialog()}
      </>
    );
  }
}

RolesViewContainer.propTypes = {
  currentUser: PropTypes.object.isRequired,
  getRole: PropTypes.func.isRequired,
  location: PropTypes.object.isRequired,
  selectedRole: PropTypes.object.isRequired,
  roleLoading: PropTypes.bool.isRequired,
  roleError: PropTypes.object,
  deleteRole: PropTypes.func.isRequired,
  deleteRoleError: PropTypes.object,
  deleteRoleLoading: PropTypes.bool.isRequired,
  updateRoleError: PropTypes.object,
  updateRoleLoading: PropTypes.bool.isRequired,
  updateRole: PropTypes.func.isRequired,
};

const mapStateToProps = state => {
  return {
    currentUser: state.authReducer.userData,
    selectedRole: state.roleReducer.selectedRole,
    roleLoading: state.roleReducer.roleLoading,
    roleError: state.roleReducer.roleError,
    deleteRoleError: state.roleReducer.deleteRoleError,
    deleteRoleLoading: state.roleReducer.deleteRoleLoading,
    updateRoleError: state.roleReducer.updateRoleError,
    updateRoleLoading: state.roleReducer.updateRoleLoading,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    getRole: name => dispatch(getRole(name)),
    deleteRole: id => dispatch(deleteRole(id)),
    updateRole: (currentRole, newRole) =>
      dispatch(updateRole(currentRole, newRole)),
  };
};

const enhance = compose(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  ),
  withRouter,
);

export default enhance(RolesViewContainer);
