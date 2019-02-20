import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { connect } from "react-redux";
import { Redirect, withRouter } from "react-router-dom";
import Typography from "@material-ui/core/Typography";

import { getUser, deleteUser } from "../../actions/user";
import Spinner from "../../components/layout/Spinner";
import { hasPermissions } from "../../utils";
import UserInfo from "../../components/users/UserInfo";
import UserInfoHeader from "../../components/users/UserInfoHeader";
import { USER_DELETE, USER_UPDATE } from "../../constants/permissions";

export class UsersViewContainer extends Component {
  state = {
    redirect: false,
  };

  componentDidMount() {
    const { match, getUser } = this.props;
    getUser(match.params.username);
  }

  deleteUser = () => {
    const { selectedUser, deleteUser } = this.props;
    deleteUser(selectedUser.id).then(() => {
      if (!this.props.deleteUserError) {
        this.setState({ redirect: true });
      }
    });
  };

  render() {
    const { userLoading, userError, selectedUser, currentUser } = this.props;
    const { redirect } = this.state;
    if (redirect) {
      return <Redirect to="/advanced/users" />;
    }
    if (userLoading) {
      return <Spinner />;
    } else if (userError) {
      return <Typography>TODO: Render an error</Typography>;
    } else {
      return (
        <>
          <UserInfoHeader
            canEdit={hasPermissions(currentUser, [USER_UPDATE])}
            canDelete={hasPermissions(currentUser, [USER_DELETE])}
            onEdit={() => {}}
            onDelete={this.deleteUser}
          />
          <UserInfo user={selectedUser} />
        </>
      );
    }
  }
}

UsersViewContainer.propTypes = {
  currentUser: PropTypes.object.isRequired,
  selectedUser: PropTypes.object.isRequired,
  userLoading: PropTypes.bool.isRequired,
  userError: PropTypes.object,
  deleteUserError: PropTypes.object,
  deleteUserLoading: PropTypes.bool.isRequired,
};

const mapStateToProps = state => {
  return {
    currentUser: state.authReducer.userData,
    selectedUser: state.userReducer.selectedUser,
    userLoading: state.userReducer.userLoading,
    userError: state.userReducer.userError,
    deleteUserError: state.userReducer.deleteUserError,
    deleteUserLoading: state.userReducer.deleteUserLoading,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    getUser: username => dispatch(getUser(username)),
    deleteUser: id => dispatch(deleteUser(id)),
  };
};

const enhance = compose(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  ),
  withRouter,
);

export default enhance(UsersViewContainer);
