import React from "react";
import PropTypes from "prop-types";
import {
  List,
  ListItem,
  ListItemText,
  Avatar,
  withStyles,
} from "@material-ui/core";
import ImageIcon from "@material-ui/icons/Image";

const styles = theme => ({
  root: {
    width: "100%",
    backgroundColor: theme.palette.background.paper,
  },
});

export function SystemList(props) {
  const { classes, systems } = props;
  const listItems = systems.map(system => (
    <ListItem key={system.id}>
      <Avatar>
        <ImageIcon />
      </Avatar>
      <ListItemText primary={system.name} secondary={system.version} />
    </ListItem>
  ));
  return <List className={classes.root}>{listItems}</List>;
}

SystemList.propTypes = {
  classes: PropTypes.object.isRequired,
  systems: PropTypes.array.isRequired,
};

export default withStyles(styles)(SystemList);
