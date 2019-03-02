import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";

import RoleForm from "../../components/roles/RoleForm";
import { toggleItemInArray } from "../../utils";

const styles = theme => ({
  error: {
    color: theme.palette.error.dark,
  },
});

export class RolesFormContainer extends Component {
  state = {
    newRoleName: {
      value: this.props.newRoleName ? this.props.newRoleName : "",
      help: "",
      error: false,
    },
    newRoleDescription: {
      value: this.props.newRoleDescription ? this.props.newRoleDescription : "",
      help: "",
      error: false,
    },
    permissions: {
      value: this.props.permissions
        ? this.props.permissions.map(p => {
            return { value: p, inherited: false };
          })
        : [],
      help: "",
      error: false,
    },
    redirect: false,
  };

  handleSubmit = e => {
    e.preventDefault();
    if (!this.validateRole()) {
      return;
    }

    const { newRoleName, newRoleDescription, permissions } = this.state;
    this.props.handleSubmit(
      newRoleName.value,
      newRoleDescription.value,
      permissions.value.map(p => p.value),
    );
  };

  validateRole = () => {
    const { newRoleName, permissions } = this.state;

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

    if (permissions.value.length === 0) {
      valid = false;
      this.setState({
        permissions: {
          value: permissions.value,
          error: true,
          help: "Please select at least one permission",
        },
      });
    }

    return valid;
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

  togglePermission = event => {
    const { permissions } = this.state;
    const {
      target: { value },
    } = event;
    this.setState({
      permissions: {
        value: toggleItemInArray(permissions.value, value, "value", v => ({
          value: v,
          inherited: false,
        })),
        error: false,
        help: "",
      },
    });
  };

  render() {
    const { classes, error, loading, header } = this.props;

    const { permissions, newRoleName, newRoleDescription } = this.state;

    return (
      <form onSubmit={this.handleSubmit}>
        {header}
        <Typography className={classes.error} align="right" variant="body1">
          {error && error.message}
        </Typography>
        <RoleForm
          permissions={permissions}
          togglePermission={this.togglePermission}
          handleFormChange={this.handleFormChange}
          saving={loading}
          newRoleDescription={newRoleDescription}
          newRoleName={newRoleName}
        />
      </form>
    );
  }
}

RolesFormContainer.propTypes = {
  classes: PropTypes.object.isRequired,
  handleSubmit: PropTypes.func.isRequired,
  loading: PropTypes.bool.isRequired,
  header: PropTypes.node.isRequired,
  error: PropTypes.object,
  newRoleName: PropTypes.string,
  newRoleDescription: PropTypes.string,
  permissions: PropTypes.array,
};

const enhance = compose(withStyles(styles));

export default enhance(RolesFormContainer);
