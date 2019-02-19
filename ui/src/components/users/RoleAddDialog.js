import React, { Component } from "react";
import PropTypes from "prop-types";
import { withStyles } from "@material-ui/core/styles";
import { compose } from "recompose";
import Button from "@material-ui/core/Button";
import CircularProgress from "@material-ui/core/CircularProgress";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogTitle from "@material-ui/core/DialogTitle";
import DialogContentText from "@material-ui/core/DialogContentText";
import RoleForm from "./RoleForm";

const styles = theme => ({
  margin: {
    ...theme.mixins.gutters(),
    paddingTop: theme.spacing.unit * 2,
    paddingBottom: theme.spacing.unit * 2,
  },
  saving: {
    position: "fixed",
    top: "50%",
    left: "50%",
    zIndex: 1,
    marginTop: -30,
    marginLeft: -30,
  },
});

export class RoleAddDialog extends Component {
  render() {
    const {
      classes,
      error,
      handleFormChange,
      open,
      onClose,
      onSave,
      permissions,
      newRoleDescription,
      newRoleName,
      saving,
      togglePermission,
    } = this.props;
    const errorContent = error ? (
      <DialogContentText color="error">{error.message}</DialogContentText>
    ) : null;
    return (
      <Dialog
        open={open}
        onClose={onClose}
        aria-labelledby="role-create-dialog-title"
        scroll="paper"
      >
        <DialogTitle id="role-create-dialog-title">Save a Role</DialogTitle>
        <div className={classes.margin}>
          {saving && <CircularProgress className={classes.saving} size={60} />}
          <DialogContentText>
            To create a role, enter a name, description, and select the
            permission you would like to assign to this role.
          </DialogContentText>
          {errorContent}
          <RoleForm
            permissions={permissions}
            togglePermission={togglePermission}
            handleFormChange={handleFormChange}
            newRoleName={newRoleName}
            newRoleDescription={newRoleDescription}
            saving={saving}
          />
          <DialogActions>
            <Button disabled={saving} onClick={onClose} color="primary">
              Cancel
            </Button>
            <Button disabled={saving} onClick={onSave} color="primary">
              Save
            </Button>
          </DialogActions>
        </div>
      </Dialog>
    );
  }
}

const fieldShape = {
  value: PropTypes.any.isRequired,
  help: PropTypes.string,
  error: PropTypes.bool.isRequired,
};

RoleAddDialog.propTypes = {
  error: PropTypes.object,
  handleFormChange: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired,
  permissions: PropTypes.shape(fieldShape).isRequired,
  newRoleDescription: PropTypes.shape(fieldShape),
  newRoleName: PropTypes.shape(fieldShape),
  saving: PropTypes.bool.isRequired,
  togglePermission: PropTypes.func.isRequired,
};

const enhance = compose(withStyles(styles));

export default enhance(RoleAddDialog);
