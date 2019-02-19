import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { withStyles } from "@material-ui/core/styles";
import FormControl from "@material-ui/core/FormControl";
import FormGroup from "@material-ui/core/FormGroup";
import FormHelperText from "@material-ui/core/FormHelperText";
import Input from "@material-ui/core/Input";
import InputLabel from "@material-ui/core/InputLabel";

const styles = theme => ({
  bottomPad: {
    paddingBottom: theme.spacing.unit * 2,
  },
  control: {
    marginLeft: theme.spacing.unit,
    marginRight: theme.spacing.unit,
  },
});

export class UserForm extends Component {
  renderInput = (name, display, inputType = "text") => {
    const { classes, handleFormChange } = this.props;
    const item = this.props[name];

    return (
      <FormControl className={classes.control}>
        <InputLabel htmlFor={name}>{display}</InputLabel>
        <Input
          id={name}
          name={name}
          aria-describedby={`${name}-helper-text`}
          onChange={handleFormChange}
          value={item.value}
          error={item.error}
          type={inputType}
        />
        <FormHelperText id={`${name}-helper-text`}>{item.help}</FormHelperText>
      </FormControl>
    );
  };

  render() {
    const { classes } = this.props;
    return (
      <div>
        <FormGroup row className={classes.bottomPad}>
          {this.renderInput("username", "Username")}
          {"currentPassword" in this.props &&
            this.renderInput("currentPassword", "Current Password", "password")}
          {this.renderInput("password", "Password", "password")}
          {this.renderInput("confirmPassword", "Confirm Password", "password")}
        </FormGroup>
      </div>
    );
  }
}

const fieldShape = {
  value: PropTypes.any.isRequired,
  error: PropTypes.bool.isRequired,
  help: PropTypes.string,
};

UserForm.propTypes = {
  classes: PropTypes.object.isRequired,
  handleFormChange: PropTypes.func.isRequired,
  username: PropTypes.shape(fieldShape).isRequired,
  password: PropTypes.shape(fieldShape).isRequired,
  confirmPassword: PropTypes.shape(fieldShape).isRequired,
  currentPassword: PropTypes.shape(fieldShape),
};

const enhance = compose(withStyles(styles));

export default enhance(UserForm);
