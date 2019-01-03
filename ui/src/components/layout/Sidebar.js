import React, { Component } from "react";
import { compose } from "recompose";
import PropTypes from "prop-types";
import { Link, withRouter } from "react-router-dom";
import { withStyles } from "@material-ui/core/styles";
import {
  Divider,
  Hidden,
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
    [theme.breakpoints.up("sm")]: {
      width: 240,
      flexShrink: 0,
    },
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
  state = {
    mobileOpen: false,
  };

  drawerContents = () => {
    const {
      classes,
      location: { pathname },
    } = this.props;
    return (
      <>
        <div className={classes.toolbar} />
        <List style={{ paddingTop: 0 }}>
          {this.routes.map(route => {
            const divider = route.divide ? <Divider /> : null;
            let selected;
            if (route.key === "systems") {
              selected = pathname === "/";
            } else {
              selected = pathname.startsWith(route.to);
            }
            return (
              <React.Fragment key={route.key}>
                {divider}
                <ListItem
                  id={`${route.key}SBLink`}
                  selected={selected}
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
      </>
    );
  };

  render() {
    const { classes, mobileOpen, toggleDrawer } = this.props;
    return (
      <>
        <Hidden xsDown>
          <Drawer
            variant="permanent"
            className={classes.drawer}
            classes={{ paper: classes.drawerPaper }}
          >
            {this.drawerContents()}
          </Drawer>
        </Hidden>
        <Hidden smUp>
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={toggleDrawer}
            classes={{ paper: classes.drawerPaper }}
          >
            {this.drawerContents()}
          </Drawer>
        </Hidden>
      </>
    );
  }
}

Sidebar.propTypes = {
  classes: PropTypes.object.isRequired,
  location: PropTypes.object.isRequired,
  mobileOpen: PropTypes.bool.isRequired,
  toggleDrawer: PropTypes.func.isRequired,
};

export default compose(
  withRouter,
  withStyles(styles),
)(Sidebar);
