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

import { createRole } from "../../actions/role";
import RoleForm from "../../components/users/RoleForm";
import { toggleItemInArray } from "../../utils";

const styles = theme => ({
  error: {
    color: theme.palette.error.dark,
  },
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
});

export class RolesAddContainer extends Component {
  state = {
    newRoleName: { value: "", help: "", error: false },
    newRoleDescription: { value: "", help: "", error: false },
    permissions: { value: [], help: "", error: false },
    redirect: false,
  };

  saveRole = e => {
    e.preventDefault();
    const { newRoleName, newRoleDescription, permissions } = this.state;
    if (!this.validateRole()) {
      return;
    }

    this.props
      .createRole(
        newRoleName.value,
        newRoleDescription.value,
        permissions.value.map(p => p.value),
      )
      .then(() => {
        if (!this.props.roleCreateError) {
          this.setState({ redirect: true });
        }
      });
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
    const {
      classes,
      roleCreateError,
      roleCreateLoading,
      location,
    } = this.props;

    const { permissions, newRoleName, newRoleDescription } = this.state;

    if (this.state.redirect) {
      const parts = location.pathname.split("/");
      const base = parts.slice(0, parts.length - 1).join("/");
      return <Redirect to={`${base}/${this.state.newRoleName.value}`} />;
    }

    const header = (
      <div className={classes.row}>
        <PersonAdd className={classes.leftIcon} fontSize="large" />
        <Typography variant="h4">New Role</Typography>
        <Button
          className={classes.rightButton}
          color="primary"
          disabled={roleCreateLoading}
          size="large"
          type="submit"
        >
          <Save className={classes.leftIcon} />
          Save
        </Button>
      </div>
    );

    return (
      <form onSubmit={this.saveRole}>
        {header}
        <Typography className={classes.error} align="right">
          {roleCreateError && roleCreateError.message}
        </Typography>
        <RoleForm
          permissions={permissions}
          togglePermission={this.togglePermission}
          handleFormChange={this.handleFormChange}
          saving={roleCreateLoading}
          newRoleDescription={newRoleDescription}
          newRoleName={newRoleName}
        />
      </form>
    );
  }
}

RolesAddContainer.propTypes = {
  classes: PropTypes.object.isRequired,
  createRole: PropTypes.func.isRequired,
  roleCreateLoading: PropTypes.bool.isRequired,
  roleCreateError: PropTypes.object,
  location: PropTypes.object.isRequired,
};

const mapStateToProps = state => {
  return {
    roleCreateLoading: state.roleReducer.roleCreateLoading,
    roleCreateError: state.roleReducer.roleCreateError,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    createRole: (name, description, permissions) =>
      dispatch(createRole(name, description, permissions)),
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

export default enhance(RolesAddContainer);
