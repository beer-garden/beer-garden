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
    if (!(name in this.props)) {
      return null;
    }

    const { classes, handleFormChange } = this.props;
    const item = this.props[name];
    const label = item.label ? item.label : display;

    return (
      <FormControl className={classes.control}>
        <InputLabel htmlFor={name}>{label}</InputLabel>
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
          {this.renderInput("currentPassword", "Current Password", "password")}
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
  label: PropTypes.string,
};

UserForm.propTypes = {
  classes: PropTypes.object.isRequired,
  handleFormChange: PropTypes.func.isRequired,
  username: PropTypes.shape(fieldShape),
  password: PropTypes.shape(fieldShape).isRequired,
  confirmPassword: PropTypes.shape(fieldShape).isRequired,
  currentPassword: PropTypes.shape(fieldShape),
};

const enhance = compose(withStyles(styles));

export default enhance(UserForm);
