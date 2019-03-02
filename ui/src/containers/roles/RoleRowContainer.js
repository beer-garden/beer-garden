import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { connect } from "react-redux";

import { hasPermissions } from "../../utils";
import { ROLE_CREATE } from "../../constants/permissions";
import { createRole, fetchRoles } from "../../actions/role";
import RoleRow from "../../components/roles/RoleRow";
import RoleDialog from "../../components/roles/RoleDialog";
import RoleAddDialog from "../../components/roles/RoleAddDialog";

export class RoleRowContainer extends Component {
  state = {
    readDialogOpen: false,
    createDialogOpen: false,
  };

  componentDidMount() {
    this.props.fetchRoles();
  }

  closeCreateDialog = () => {
    this.setState({ createDialogOpen: false });
  };

  closeReadDialog = () => {
    this.setState({ readDialogOpen: false });
  };

  openCreateDialog = () => {
    this.setState({ createDialogOpen: true });
  };

  openReadDialog = () => {
    this.setState({ readDialogOpen: true });
  };

  saveRole = () => {
    const {
      afterSaveRole,
      newRoleName,
      newRoleDescription,
      permissions,
      createRole,
      validateRole,
    } = this.props;

    if (!validateRole()) {
      return;
    }

    createRole(
      newRoleName.value,
      newRoleDescription.value,
      permissions.value.map(p => p.value),
    ).then(result => {
      if (!this.props.roleCreateError) {
        this.closeCreateDialog();
        afterSaveRole(result);
      }
    });
  };

  render() {
    const {
      currentUser,
      roleCreateError,
      roleCreateLoading,
      roles,
      rolesLoading,
      rolesError,

      selectedRoles,
      handleRoleClick,
      handleFormChange,
      permissions,
      newRoleDescription,
      newRoleName,
      togglePermission,
      triggerRoleSave,
    } = this.props;

    const canAdd = hasPermissions(currentUser, [ROLE_CREATE]);
    const { readDialogOpen, createDialogOpen } = this.state;
    let createOpen;
    if (triggerRoleSave) {
      createOpen = true;
    } else {
      createOpen = createDialogOpen;
    }
    return (
      <>
        <RoleRow
          selectedRoles={selectedRoles}
          handleRoleClick={handleRoleClick}
          handleInheritRoleClick={this.openReadDialog}
          edit={true}
        />
        <RoleDialog
          canAdd={canAdd}
          open={readDialogOpen}
          onClose={this.closeReadDialog}
          roles={roles}
          selectedRoles={selectedRoles}
          rolesLoading={rolesLoading}
          rolesError={rolesError}
          handleSelectRole={handleRoleClick}
          handleAddRoleClick={this.openCreateDialog}
        />
        {canAdd && (
          <RoleAddDialog
            error={roleCreateError}
            handleFormChange={handleFormChange}
            open={createOpen}
            onClose={this.closeCreateDialog}
            onSave={this.saveRole}
            permissions={permissions}
            newRoleDescription={newRoleDescription}
            newRoleName={newRoleName}
            saving={roleCreateLoading}
            togglePermission={togglePermission}
          />
        )}
      </>
    );
  }
}

const fieldShape = {
  value: PropTypes.any.isRequired,
  help: PropTypes.string,
  error: PropTypes.bool.isRequired,
};

RoleRowContainer.propTypes = {
  afterSaveRole: PropTypes.func,
  selectedRoles: PropTypes.array.isRequired,
  handleRoleClick: PropTypes.func.isRequired,
  handleFormChange: PropTypes.func,
  permissions: PropTypes.shape(fieldShape).isRequired,
  newRoleDescription: PropTypes.shape(fieldShape),
  newRoleName: PropTypes.shape(fieldShape),
  togglePermission: PropTypes.func,
  triggerRoleSave: PropTypes.bool.isRequired,
  validateRole: PropTypes.func,
};

const mapStateToProps = state => {
  return {
    currentUser: state.authReducer.userData,
    roleCreateError: state.roleReducer.roleCreateError,
    roleCreateLoading: state.roleReducer.roleCreateLoading,
    roles: state.roleReducer.roles,
    rolesLoading: state.roleReducer.rolesLoading,
    rolesError: state.roleReducer.rolesError,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    fetchRoles: () => dispatch(fetchRoles()),
    createRole: (name, description, permissions) =>
      dispatch(createRole(name, description, permissions)),
  };
};

const enhance = compose(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  ),
);

export default enhance(RoleRowContainer);
