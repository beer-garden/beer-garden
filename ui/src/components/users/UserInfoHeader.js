import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { withStyles } from "@material-ui/core/styles";
import Button from "@material-ui/core/Button";
import Hidden from "@material-ui/core/Hidden";
import Typography from "@material-ui/core/Typography";
import AccountBox from "@material-ui/icons/AccountBox";
import Close from "@material-ui/icons/Close";
import Delete from "@material-ui/icons/Delete";
import Edit from "@material-ui/icons/Edit";
import Save from "@material-ui/icons/Save";

const styles = theme => ({
  leftIcon: { marginRight: theme.spacing.unit },
  rightIcon: { marginLeft: theme.spacing.unit },
  error: { color: theme.palette.error.dark },
  headerRow: { display: "flex", flexDirection: "row" },
  rightButton: { marginLeft: "auto" },
});

export class UserInfoHeader extends Component {
  renderTitle = () => {
    const { classes } = this.props;
    return (
      <>
        <Hidden xsDown>
          <AccountBox className={classes.leftIcon} fontSize="large" />
          <Typography variant="h4">User Information</Typography>
        </Hidden>
        <Hidden smUp>
          <Typography variant="h4">User Info</Typography>
        </Hidden>
      </>
    );
  };

  renderButtons = () => {
    const {
      classes,
      canEdit,
      canDelete,
      editing,
      onCancelEdit,
      onEdit,
      onDelete,
      deleting,
      saving,
    } = this.props;

    const saveButton = (
      <Button type="submit" color="primary" disabled={saving}>
        <Hidden xsDown>Save</Hidden>
        <Save className={classes.rightIcon} fontSize="small" />
      </Button>
    );

    const editButton = (
      <Button color="primary" onClick={onEdit} disabled={deleting}>
        <Hidden xsDown>Edit</Hidden>
        <Edit className={classes.rightIcon} fontSize="small" />
      </Button>
    );

    const cancelButton = (
      <Button color="primary" onClick={onCancelEdit}>
        <Hidden xsDown>Cancel</Hidden>
        <Close className={classes.rightIcon} fontSize="small" />
      </Button>
    );

    const deleteButton = (
      <Button className={classes.error} onClick={onDelete} disabled={deleting}>
        <Hidden xsDown>Delete</Hidden>
        <Delete className={classes.rightIcon} fontSize="small" />
      </Button>
    );

    let rightButton = null;
    let leftButton = null;

    if (editing) {
      leftButton = saveButton;
      rightButton = cancelButton;
    } else if (canEdit && canDelete) {
      rightButton = editButton;
      leftButton = deleteButton;
    } else if (canEdit) {
      rightButton = editButton;
    } else if (canDelete) {
      leftButton = deleteButton;
    }

    return (
      <>
        {leftButton}
        {rightButton}
      </>
    );
  };

  renderError() {
    const { classes, errorMessage } = this.props;
    if (!errorMessage) {
      return null;
    }
    return (
      <Typography variant="body1" align="right" className={classes.error}>
        {errorMessage}
      </Typography>
    );
  }

  render() {
    const { classes } = this.props;

    return (
      <>
        <div className={classes.headerRow}>
          {this.renderTitle()}
          <div className={classes.rightButton}>{this.renderButtons()}</div>
        </div>
        {this.renderError()}
      </>
    );
  }
}

UserInfoHeader.propTypes = {
  editing: PropTypes.bool.isRequired,
  canEdit: PropTypes.bool.isRequired,
  canDelete: PropTypes.bool.isRequired,
  deleting: PropTypes.bool.isRequired,
  onCancelEdit: PropTypes.func.isRequired,
  onEdit: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  errorMessage: PropTypes.string.isRequired,
  saving: PropTypes.bool.isRequired,
};

const enhance = compose(withStyles(styles));

export default enhance(UserInfoHeader);
