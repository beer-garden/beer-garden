import React, { Component } from "react";
import PropTypes from "prop-types";
import {
  Typography,
  Grid,
  Paper,
  CircularProgress,
  Avatar,
  Button,
  FormControl,
  Input,
  InputLabel,
} from "@material-ui/core";
import LockIcon from "@material-ui/icons/LockOutlined";
import withStyles from "@material-ui/core/styles/withStyles";

const styles = theme => ({
  paper: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: `${theme.spacing.unit * 2}px ${theme.spacing.unit * 3}px ${theme
      .spacing.unit * 3}px`,
  },
  avatar: {
    margin: theme.spacing.unit,
    backgroundColor: theme.palette.secondary.main,
  },
  form: {
    width: "100%", // Fix IE 11 issue.
    marginTop: theme.spacing.unit,
  },
  submit: {
    marginTop: theme.spacing.unit * 3,
  },
  progress: {
    position: "relative",
    top: -58,
    left: 0,
    zIndex: 1,
    marginBottom: -58,
  },
});

export class Login extends Component {
  state = {
    username: null,
    password: null,
  };

  onSubmit = e => {
    e.preventDefault();
    this.props.login(this.state);
  };

  handleChange = e => {
    this.setState({ [e.target.name]: e.target.value });
  };

  render() {
    const {
      guestLoginEnabled,
      classes,
      loading,
      error,
      guestLogin,
    } = this.props;

    return (
      <Grid item xs={12} sm={6}>
        <Paper className={classes.paper}>
          <Avatar className={classes.avatar}>
            <LockIcon />
          </Avatar>
          {loading && (
            <CircularProgress className={classes.progress} size={60} />
          )}
          <Typography component="h1" variant="h5">
            Sign in
          </Typography>
          <form
            id="loginForm"
            className={classes.form}
            onSubmit={this.onSubmit}
          >
            <FormControl margin="normal" required fullWidth>
              <InputLabel htmlFor="username">Username</InputLabel>
              <Input
                id="username"
                name="username"
                autoComplete="username"
                autoFocus
                disabled={loading}
                onChange={this.handleChange}
              />
            </FormControl>
            <FormControl margin="normal" required fullWidth>
              <InputLabel htmlFor="password">Password</InputLabel>
              <Input
                name="password"
                type="password"
                id="password"
                autoComplete="current-password"
                disabled={loading}
                onChange={this.handleChange}
              />
            </FormControl>
            <Button
              id="userLoginBtn"
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              className={classes.submit}
              disabled={loading}
            >
              Sign in
            </Button>
            {guestLoginEnabled ? (
              <Button
                id="guestLoginBtn"
                onClick={() => guestLogin(this.state)}
                fullWidth
                variant="contained"
                color="default"
                className={classes.submit}
                disabled={loading}
              >
                Continue as Guest
              </Button>
            ) : null}
          </form>
          <br />
          {error ? (
            <Typography id="errorMessage" variant="body1" color="error">
              Error Message: {error.message}
            </Typography>
          ) : null}
        </Paper>
      </Grid>
    );
  }
}

Login.propTypes = {
  classes: PropTypes.object.isRequired,
  loading: PropTypes.bool.isRequired,
  login: PropTypes.func.isRequired,
  guestLoginEnabled: PropTypes.bool.isRequired,
  guestLogin: function(props, propName, componentName) {
    if (
      props["guestLoginEnabled"] === true &&
      (props[propName] === undefined || typeof props[propName] !== "function")
    ) {
      return new Error("Please provide a guest login function.");
    }
  },
  error: PropTypes.object,
};

export default withStyles(styles)(Login);
