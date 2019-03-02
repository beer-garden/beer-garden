import React, { Component } from "react";
import PropTypes from "prop-types";
import Dialog from "@material-ui/core/Dialog";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogTitle from "@material-ui/core/DialogTitle";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import Group from "@material-ui/icons/Group";
import GroupAdd from "@material-ui/icons/GroupAdd";

import Spinner from "../layout/Spinner";

export class RoleDialog extends Component {
  renderDialogContent = () => {
    const {
      canAdd,
      roles,
      selectedRoles,
      rolesError,
      rolesLoading,
      handleAddRoleClick,
      handleSelectRole,
    } = this.props;

    if (rolesError) {
      return (
        <DialogContent>
          <DialogContentText color="error">
            Oops, couldn't read roles. {rolesError.message}
          </DialogContentText>
        </DialogContent>
      );
    } else if (rolesLoading) {
      return (
        <DialogContent>
          <Spinner />
        </DialogContent>
      );
    }

    return (
      <List>
        {roles.map(role => {
          let iconColor = "inherit";
          let primaryTextColor = "textPrimary";
          let secondaryTextColor = "textSecondary";
          if (selectedRoles.find(r => r.name === role.name)) {
            iconColor = "primary";
            primaryTextColor = "primary";
            secondaryTextColor = "primary";
          }
          return (
            <ListItem
              button
              onClick={() => handleSelectRole(role)}
              key={role.name}
            >
              <ListItemIcon>
                <Group color={iconColor} />
              </ListItemIcon>
              <ListItemText
                primaryTypographyProps={{ color: primaryTextColor }}
                secondaryTypographyProps={{ color: secondaryTextColor }}
                primary={role.name}
                secondary={
                  role.description
                    ? role.description
                    : "No description provided"
                }
              />
            </ListItem>
          );
        })}
        {canAdd && (
          <ListItem button onClick={handleAddRoleClick}>
            <ListItemIcon>
              <GroupAdd />
            </ListItemIcon>
            <ListItemText primary="create new role" />
          </ListItem>
        )}
      </List>
    );
  };

  render() {
    const { open, onClose } = this.props;
    return (
      <Dialog
        onClose={onClose}
        aria-labelledby="simple-dialog-title"
        scroll="paper"
        open={open}
      >
        <DialogTitle id="simple-dialog-title">Select a Role</DialogTitle>
        {this.renderDialogContent()}
      </Dialog>
    );
  }
}

RoleDialog.propTypes = {
  canAdd: PropTypes.bool.isRequired,
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  roles: PropTypes.array.isRequired,
  selectedRoles: PropTypes.array.isRequired,
  rolesError: PropTypes.object,
  rolesLoading: PropTypes.bool.isRequired,
  handleSelectRole: PropTypes.func.isRequired,
  handleAddRoleClick: function(props, propName, componentName) {
    if (
      props["canAdd"] &&
      (props[propName] === undefined ||
        props[propName] === null ||
        typeof props[propName] !== "function")
    ) {
      return new Error(
        "When canAdd is true, handleAddRoleClick must be a function",
      );
    }
  },
};

export default RoleDialog;
