import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Divider from '@material-ui/core/Divider';
import Drawer from '@material-ui/core/Drawer';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import FolderIcon from '@material-ui/icons/Folder';
import ViewModuleIcon from '@material-ui/icons/ViewModule';
import StorageIcon from '@material-ui/icons/Storage';
import ScheduleIcon from '@material-ui/icons/Schedule';
import SettingsIcon from '@material-ui/icons/Settings';

const styles = theme => ({
  drawer: {
    flexShrink: 0
  },
  toolbar: theme.mixins.toolbar
});

class Sidebar extends Component {
  render() {
    const { classes } = this.props;
    return (
      <Drawer variant="permanent" className={classes.drawer}>
        <div className={classes.toolbar} />
        <List>
          <ListItem button key="systems">
            <ListItemIcon>
              <FolderIcon />{' '}
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
  classes: PropTypes.object.isRequired
};

export default withStyles(styles)(Sidebar);
