import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import {
  AppBar,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
  IconButton,
} from '@material-ui/core';
import { AccountCircle } from '@material-ui/icons';

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

  render() {
    const { classes, config, user } = this.props;
    const { anchorEl } = this.state;
    const open = Boolean(anchorEl);

    const userIcon = (
      <>
        <IconButton
          aria-owns={open ? 'menu-appbar' : undefined}
          aria-haspopup="true"
          onClick={this.handleMenu}
          color="inherit"
        >
          <AccountCircle />
        </IconButton>
        <Menu
          id="menu-appbar"
          anchorEl={anchorEl}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          open={open}
          onClose={this.handleClose}
        >
          <MenuItem onClick={this.handleClose}>User Settings</MenuItem>
        </Menu>
      </>
    );
    return (
      <AppBar position="static" color="primary" className={classes.appBar}>
        <Toolbar>
          <Typography variant="h6" color="inherit" style={{ flex: 1 }}>
            {config.applicationName}
          </Typography>
          {user ? userIcon : null}
        </Toolbar>
      </AppBar>
    );
  }
}

const mapStateToProps = state => {
  return {
    config: state.configReducer.config,
    user: state.authReducer.user,
  };
};

const mapDispatchToProps = dispatch => {
  return {};
};

Topbar.propTypes = {
  classes: PropTypes.object.isRequired,
  config: PropTypes.object.isRequired,
  user: PropTypes.object,
};

export default connect(
  mapStateToProps,
  mapDispatchToProps,
)(withStyles(styles)(Topbar));
