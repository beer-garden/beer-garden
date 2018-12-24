import React, { Component } from "react";
import { compose } from "recompose";
import PropTypes from "prop-types";
import { Link, withRouter } from "react-router-dom";
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
  routes = [
    { to: "/", key: "systems", icon: <FolderIcon />, text: "Systems" },
    {
      to: "/commands",
      key: "commands",
      icon: <ViewModuleIcon />,
      text: "Commands",
    },
    {
      to: "/requests",
      key: "requests",
      icon: <StorageIcon />,
      text: "Requests",
    },
    {
      to: "/scheduler",
      key: "scheduler",
      icon: <ScheduleIcon />,
      text: "Scheduler",
    },
    {
      to: "/advanced",
      key: "advanced",
      icon: <SettingsIcon />,
      text: "Advanced",
      divide: true,
    },
  ];

  //TODO: Make sidebar responsive
  render() {
    const {
      classes,
      location: { pathname },
    } = this.props;
    return (
      <Drawer
        variant="permanent"
        className={classes.drawer}
        classes={{ paper: classes.drawerPaper }}
      >
        <div className={classes.toolbar} />
        <List style={{ paddingTop: 0 }}>
          {this.routes.map(route => {
            const divider = route.divide ? <Divider /> : null;
            return (
              <React.Fragment key={route.key}>
                {divider}
                <ListItem
                  id={`${route.key}SBLink`}
                  selected={route.to === pathname}
                  button
                  component={Link}
                  to={route.to}
                  key={route.key}
                >
                  <ListItemIcon>{route.icon}</ListItemIcon>
                  <ListItemText primary={route.text} />
                </ListItem>
              </React.Fragment>
            );
          })}
        </List>
      </Drawer>
    );
  }
}

Sidebar.propTypes = {
  classes: PropTypes.object.isRequired,
  location: PropTypes.object.isRequired,
};

export default compose(
  withRouter,
  withStyles(styles),
)(Sidebar);
