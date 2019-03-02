import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { withStyles } from "@material-ui/core/styles";
import FormControl from "@material-ui/core/FormControl";
import FormHelperText from "@material-ui/core/FormHelperText";
import FormGroup from "@material-ui/core/FormGroup";
import Input from "@material-ui/core/Input";
import InputLabel from "@material-ui/core/InputLabel";
import PermissionList from "./PermissionList";

const styles = theme => ({
  bottomPad: { paddingBottom: theme.spacing.unit * 2 },
  control: { marginLeft: theme.spacing.unit, marginRight: theme.spacing.unit },
});

export class RoleForm extends Component {
  renderInput = (name, display, inputType = "text") => {
    const { classes, handleFormChange, saving } = this.props;
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
          disabled={saving}
        />
        <FormHelperText id={`${name}-helper-text`}>{item.help}</FormHelperText>
      </FormControl>
    );
  };

  render() {
    const { classes, permissions, togglePermission, saving } = this.props;
    return (
      <div>
        <FormGroup row className={classes.bottomPad}>
          {this.renderInput("newRoleName", "Name")}
          {this.renderInput("newRoleDescription", "Description")}
        </FormGroup>
        <PermissionList
          edit={true}
          permissions={permissions.value}
          togglePermission={togglePermission}
          errorMessage={permissions.help}
          disabled={saving}
        />
      </div>
    );
  }
}

const fieldShape = {
  value: PropTypes.any.isRequired,
  error: PropTypes.bool.isRequired,
  help: PropTypes.string,
};

RoleForm.propTypes = {
  classes: PropTypes.object.isRequired,
  permissions: PropTypes.shape(fieldShape).isRequired,
  togglePermission: PropTypes.func.isRequired,
  handleFormChange: PropTypes.func.isRequired,
  newRoleName: PropTypes.shape(fieldShape),
  newRoleDescription: PropTypes.shape(fieldShape),
  saving: PropTypes.bool.isRequired,
};

const enhance = compose(withStyles(styles));

export default enhance(RoleForm);
