import React, { Component } from "react";
import PropTypes from "prop-types";
import { withRouter } from "react-router-dom";
import { connect } from "react-redux";
import { compose } from "recompose";
import { Typography, withStyles } from "@material-ui/core";

import { fetchUsers, getUser } from "../../actions/user";
import Spinner from "../../components/layout/Spinner";
import UserList from "../../components/users/UserList";
import {
  USER_CREATE,
  ROLE_CREATE,
  ROLE_READ,
} from "../../constants/permissions";
import { hasPermissions } from "../../utils";
import UserListHeader from "../../components/users/UserListHeader";

const styles = theme => ({
  error: { color: theme.palette.error.dark },
});

export class UsersListContainer extends Component {
  state = {
    filterText: "",
  };

  componentDidMount() {
    this.props.fetchUsers();
  }

  filterUsers(users, filterText) {
    return users.filter(user => user.username.includes(filterText));
  }

  changeFilter = event => {
    this.setState({ filterText: event.target.value });
  };

  renderContents() {
    const { classes, usersLoading, usersError, users } = this.props;
    if (usersLoading) {
      return <Spinner />;
    } else if (usersError) {
      return (
        <Typography variant="body1" className={classes.error}>
          TODO: render a useful error.
        </Typography>
      );
    }
    const filteredUsers = this.filterUsers(users, this.state.filterText);
    return <UserList users={filteredUsers} />;
  }

  render() {
    const { currentUser, match } = this.props;
    const { filterText } = this.state;
    const canAdd =
      hasPermissions(currentUser, [USER_CREATE, ROLE_READ]) ||
      hasPermissions(currentUser, [USER_CREATE, ROLE_CREATE]);
    return (
      <>
        <UserListHeader
          canAdd={canAdd}
          addRoute={`${match.url}/add`}
          filterText={filterText}
          onFilterChange={this.changeFilter}
        />
        {this.renderContents()}
      </>
    );
  }
}

UsersListContainer.propTypes = {
  classes: PropTypes.object.isRequired,
  currentUser: PropTypes.object.isRequired,
  users: PropTypes.array.isRequired,
  usersLoading: PropTypes.bool.isRequired,
  usersError: PropTypes.object,
  fetchUsers: PropTypes.func.isRequired,
  match: PropTypes.object.isRequired,
};

const mapStateToProps = state => {
  return {
    currentUser: state.authReducer.userData,
    users: state.userReducer.users,
    usersLoading: state.userReducer.usersLoading,
    usersError: state.userReducer.usersError,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    fetchUsers: () => dispatch(fetchUsers()),
    getUser: id => dispatch(getUser(id)),
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

export default enhance(UsersListContainer);
