import React, { Component } from "react";
import PropTypes from "prop-types";
import { withRouter } from "react-router-dom";
import { connect } from "react-redux";
import { compose } from "recompose";
import { Typography, withStyles } from "@material-ui/core";

import { fetchRoles } from "../../actions/role";
import Spinner from "../../components/layout/Spinner";
import RoleList from "../../components/roles/RoleList";
import { ROLE_CREATE } from "../../constants/permissions";
import { hasPermissions } from "../../utils";
import RoleListHeader from "../../components/roles/RoleListHeader";

const styles = theme => ({
  error: { color: theme.palette.error.dark },
});

export class RolesListContainer extends Component {
  state = {
    filterText: "",
  };

  componentDidMount() {
    this.props.fetchRoles();
  }

  filterRoles(roles, filterText) {
    return roles.filter(role => role.name.includes(filterText));
  }

  changeFilter = event => {
    this.setState({ filterText: event.target.value });
  };

  renderContents() {
    const { classes, rolesLoading, rolesError, roles } = this.props;
    if (rolesLoading) {
      return <Spinner />;
    } else if (rolesError) {
      return (
        <Typography variant="body1" className={classes.error}>
          TODO: render a useful error.
        </Typography>
      );
    }
    const filteredRoles = this.filterRoles(roles, this.state.filterText);
    return <RoleList roles={filteredRoles} />;
  }

  render() {
    const { currentUser, match } = this.props;
    const { filterText } = this.state;
    return (
      <>
        <RoleListHeader
          canAdd={hasPermissions(currentUser, [ROLE_CREATE])}
          addRoute={`${match.url}/add`}
          filterText={filterText}
          onFilterChange={this.changeFilter}
        />
        {this.renderContents()}
      </>
    );
  }
}

RolesListContainer.propTypes = {
  classes: PropTypes.object.isRequired,
  currentUser: PropTypes.object.isRequired,
  roles: PropTypes.array.isRequired,
  rolesLoading: PropTypes.bool.isRequired,
  rolesError: PropTypes.object,
  fetchRoles: PropTypes.func.isRequired,
  match: PropTypes.object.isRequired,
};

const mapStateToProps = state => {
  return {
    currentUser: state.authReducer.userData,
    roles: state.roleReducer.roles,
    rolesLoading: state.roleReducer.rolesLoading,
    rolesError: state.roleReducer.rolesError,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    fetchRoles: () => dispatch(fetchRoles()),
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

export default enhance(RolesListContainer);
