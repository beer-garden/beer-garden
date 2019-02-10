import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { compose } from "recompose";
import { Button, Grid, Paper, Typography, withStyles } from "@material-ui/core";
import SearchIcon from "@material-ui/icons/Search";
import AddIcon from "@material-ui/icons/Add";

import { fetchUsers } from "../../actions/user";
import Spinner from "../../components/layout/Spinner";
import UserList from "../../components/advanced/UserList";
import TextField from "@material-ui/core/TextField";
import InputAdornment from "@material-ui/core/InputAdornment";
import { hasPermissions } from "../../utils";

const styles = theme => ({
  root: {
    ...theme.mixins.gutters(),
    paddingTop: theme.spacing.unit * 2,
    paddingBottom: theme.spacing.unit * 2,
  },
  icon: {
    marginLeft: theme.spacing.unit,
  },
  rightButton: {
    marginLeft: "auto",
  },
  headerRow: {
    display: "flex",
    flexDirection: "row",
    marginBottom: "10px",
  },
});

export class UsersContainer extends Component {
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

  renderHeader() {
    const { filterText } = this.state;
    const { classes, currentUser } = this.props;
    let addButton = null;
    if (hasPermissions(currentUser, ["bg-user-create"])) {
      addButton = (
        <Button color="primary" className={classes.rightButton}>
          Add User
          <AddIcon fontSize="small" className={classes.icon} />
        </Button>
      );
    }
    return (
      <div>
        <Typography variant="h4" gutterBottom>
          User Management
        </Typography>
        <div className={classes.headerRow}>
          <TextField
            label="Search users..."
            value={filterText}
            onChange={this.changeFilter}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
          {addButton}
        </div>
      </div>
    );
  }

  renderContents() {
    const { usersLoading, users } = this.props;
    if (usersLoading) {
      return <Spinner />;
    }
    const filteredUsers = this.filterUsers(users, this.state.filterText);
    if (filteredUsers.length === 0) {
      return <Typography variant="body1">No users could be found.</Typography>;
    } else {
      return <UserList users={users} />;
    }
  }

  render() {
    const { classes } = this.props;
    return (
      <Grid container spacing={24}>
        <Grid item xs={12}>
          <Paper className={classes.root}>
            {this.renderHeader()}
            {this.renderContents()}
          </Paper>
        </Grid>
      </Grid>
    );
  }
}

UsersContainer.propTypes = {
  classes: PropTypes.object.isRequired,
  currentUser: PropTypes.object.isRequired,
  users: PropTypes.array.isRequired,
  usersLoading: PropTypes.bool.isRequired,
  usersError: PropTypes.object,
  fetchUsers: PropTypes.func.isRequired,
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
  };
};

const enhance = compose(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  ),
  withStyles(styles),
);

export default enhance(UsersContainer);
