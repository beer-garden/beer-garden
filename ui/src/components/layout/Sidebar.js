import React, { Component } from "react";
import PropTypes from "prop-types";
import { withStyles } from "@material-ui/core/styles";
import {
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from "@material-ui/core";
import FolderIcon from "@material-ui/icons/Folder";
import ViewModuleIcon from "@material-ui/icons/ViewModule";
import StorageIcon from "@material-ui/icons/Storage";
import ScheduleIcon from "@material-ui/icons/Schedule";
import SettingsIcon from "@material-ui/icons/Settings";

const styles = theme => ({
  drawer: {
    width: 240,
    flexShrink: 0,
  },
  drawerPaper: {
    width: 240,
  },
  toolbar: theme.mixins.toolbar,
});

export class Sidebar extends Component {
  render() {
    const { classes } = this.props;
    return (
      <Drawer
        variant="permanent"
        className={classes.drawer}
        classes={{ paper: classes.drawerPaper }}
      >
        <div className={classes.toolbar} />
        <List>
          <ListItem button key="systems">
            <ListItemIcon>
              <FolderIcon />
            </ListItemIcon>
            <ListItemText primary="Systems" />
          </ListItem>
          <ListItem button key="commands">
            <ListItemIcon>
              <ViewModuleIcon />
            </ListItemIcon>
            <ListItemText primary="Commands" />
          </ListItem>
          <ListItem button key="requests">
            <ListItemIcon>
              <StorageIcon />
            </ListItemIcon>
            <ListItemText primary="Requests" />
          </ListItem>
          <ListItem button key="scheduler">
            <ListItemIcon>
              <ScheduleIcon />
            </ListItemIcon>
            <ListItemText primary="Scheduler" />
          </ListItem>
          <Divider />
          <ListItem button key="advanced">
            <ListItemIcon>
              <SettingsIcon />
            </ListItemIcon>
            <ListItemText primary="Advanced" />
          </ListItem>
        </List>
      </Drawer>
    );
  }
}

Sidebar.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(Sidebar);
