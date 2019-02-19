import React from "react";
import PropTypes from "prop-types";
import {
  List,
  ListItem,
  ListItemText,
  Avatar,
  withStyles,
} from "@material-ui/core";
import AccountCircle from "@material-ui/icons/AccountCircle";

const styles = theme => ({
  root: {
    width: "100%",
    backgroundColor: theme.palette.background.paper,
  },
});

export function UserList(props) {
  const { classes, users } = props;
  const listItems = users.map(user => {
    const roles = "Roles: " + user.roles.map(r => r.name).join(", ");
    return (
      <ListItem button key={user.id}>
        <Avatar>
          <AccountCircle />
        </Avatar>
        <ListItemText primary={user.username} secondary={roles} />
      </ListItem>
    );
  });
  return (
    <List component="nav" className={classes.root}>
      {listItems}
    </List>
  );
}

UserList.propTypes = {
  classes: PropTypes.object.isRequired,
  users: PropTypes.array.isRequired,
};

export default withStyles(styles)(UserList);
