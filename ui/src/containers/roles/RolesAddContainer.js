import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { compose } from "recompose";
import { Redirect, withRouter } from "react-router-dom";
import { withStyles } from "@material-ui/core/styles";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import HowToReg from "@material-ui/icons/HowToReg";
import Save from "@material-ui/icons/Save";

import { createRole } from "../../actions/role";
import RolesFormContainer from "./RolesFormContainer";

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
    redirect: false,
    newRoleName: "",
  };

  saveRole = (name, description, permissions) => {
    this.props.createRole(name, description, permissions).then(() => {
      if (!this.props.roleCreateError) {
        this.setState({ redirect: true, newRoleName: name });
      }
    });
  };

  render() {
    const {
      classes,
      roleCreateError,
      roleCreateLoading,
      location,
    } = this.props;

    if (this.state.redirect) {
      const parts = location.pathname.split("/");
      const base = parts.slice(0, parts.length - 1).join("/");
      return <Redirect to={`${base}/${this.state.newRoleName}`} />;
    }

    const header = (
      <div className={classes.row}>
        <HowToReg className={classes.leftIcon} fontSize="large" />
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
      <RolesFormContainer
        handleSubmit={this.saveRole}
        loading={roleCreateLoading}
        header={header}
        error={roleCreateError}
      />
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
