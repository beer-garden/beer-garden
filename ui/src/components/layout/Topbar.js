import React, { Component } from "react";
import PropTypes from "prop-types";
import { withStyles } from "@material-ui/core/styles";
import {
  AppBar,
  Menu,
  MenuItem,
  Switch,
  Toolbar,
  Typography,
  IconButton,
} from "@material-ui/core";
import { AccountCircle } from "@material-ui/icons";

const styles = theme => ({
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
  },
});

export class Topbar extends Component {
  state = {
    anchorEl: null,
  };

  handleMenu = event => {
    this.setState({ anchorEl: event.currentTarget });
  };

  handleClose = event => {
    this.setState({ anchorEl: null });
  };

  toggleTheme = () => {
    const { themeName, setUserTheme } = this.props;
    if (themeName === "dark") {
      setUserTheme("light");
    } else {
      setUserTheme("dark");
    }
  };

  userIcon = () => {
    const { anchorEl } = this.state;
    const { themeName } = this.props;
    const open = Boolean(anchorEl);
    const themeChecked = themeName === "dark";
    return (
      <>
        <IconButton
          aria-owns={open ? "menu-appbar" : undefined}
          aria-haspopup="true"
          onClick={this.handleMenu}
          color="inherit"
        >
          <AccountCircle />
        </IconButton>
        <Menu
          id="menu-appbar"
          anchorEl={anchorEl}
          anchorOrigin={{ vertical: "top", horizontal: "right" }}
          transformOrigin={{ vertical: "top", horizontal: "right" }}
          open={open}
          onClose={this.handleClose}
        >
          <MenuItem onClick={this.toggleTheme}>
            <Switch checked={themeChecked} />
          </MenuItem>
        </Menu>
      </>
    );
  };

  render() {
    const { classes, appName, isAuthenticated } = this.props;

    return (
      <AppBar position="fixed" color="primary" className={classes.appBar}>
        <Toolbar>
          <Typography variant="h6" color="inherit" style={{ flex: 1 }}>
            {appName}
          </Typography>
          {isAuthenticated ? this.userIcon() : null}
        </Toolbar>
      </AppBar>
    );
  }
}

Topbar.propTypes = {
  appName: PropTypes.string.isRequired,
  isAuthenticated: PropTypes.bool.isRequired,
  classes: PropTypes.object.isRequired,
  themeName: PropTypes.string,
  setUserTheme: PropTypes.func,
};

export default withStyles(styles)(Topbar);
