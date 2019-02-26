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
import HowToReg from "@material-ui/icons/HowToReg";

const styles = theme => ({
  root: {
    width: "100%",
    backgroundColor: theme.palette.background.paper,
  },
});

export function RoleList(props) {
  const { match, classes, roles } = props;
  const listItems = roles.map(role => {
    const permissions = "Permissions: " + role.permissions.join(", ");
    return (
      <ListItem
        button
        key={role.id}
        component={Link}
        to={`${match.url}/${role.name}`}
      >
        <Avatar>
          <HowToReg />
        </Avatar>
        <ListItemText primary={role.name} secondary={permissions} />
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
    return <Typography variant="body1">No roles could be found.</Typography>;
  }
}

RoleList.propTypes = {
  classes: PropTypes.object.isRequired,
  roles: PropTypes.array.isRequired,
  match: PropTypes.object.isRequired,
};

const enhance = compose(
  withStyles(styles),
  withRouter,
);

export default enhance(RoleList);
