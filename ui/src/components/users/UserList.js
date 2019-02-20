import React from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { Link, withRouter } from "react-router-dom";
import { withStyles } from "@material-ui/core/styles";
import Avatar from "@material-ui/core/Avatar";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemText from "@material-ui/core/ListItemText";
import Typography from "@material-ui/core/Typography";
import AccountCircle from "@material-ui/icons/AccountCircle";

const styles = theme => ({
  root: {
    width: "100%",
    backgroundColor: theme.palette.background.paper,
  },
});

export function UserList(props) {
  const { match, classes, users } = props;
  const listItems = users.map(user => {
    const roles = "Roles: " + user.roles.map(r => r.name).join(", ");
    return (
      <ListItem
        button
        key={user.id}
        component={Link}
        to={`${match.url}/${user.username}`}
      >
        <Avatar>
          <AccountCircle />
        </Avatar>
        <ListItemText primary={user.username} secondary={roles} />
      </ListItem>
    );
  });

  if (listItems.length > 0) {
    return (
      <List component="nav" className={classes.root}>
        {listItems}
      </List>
    );
  } else {
    return <Typography variant="body1">No users could be found.</Typography>;
  }
}

UserList.propTypes = {
  classes: PropTypes.object.isRequired,
  users: PropTypes.array.isRequired,
  match: PropTypes.object.isRequired,
};

const enhance = compose(
  withStyles(styles),
  withRouter,
);

export default enhance(UserList);
