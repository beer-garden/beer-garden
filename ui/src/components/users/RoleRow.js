import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { withStyles } from "@material-ui/core/styles";
import Chip from "@material-ui/core/Chip";
import Divider from "@material-ui/core/Divider";
import Fab from "@material-ui/core/Fab";
import Tooltip from "@material-ui/core/Tooltip";
import Typography from "@material-ui/core/Typography";

import Add from "@material-ui/icons/Add";

const styles = theme => ({
  topPad: {
    paddingTop: theme.spacing.unit,
  },
  bottomPad: {
    paddingBottom: theme.spacing.unit * 2,
  },
  chip: {
    marginRight: theme.spacing.unit,
  },
});

export class RoleRow extends Component {
  renderRoleChips = () => {
    const { classes, selectedRoles, handleRoleClick } = this.props;

    const roleChips = selectedRoles.map(role => {
      return (
        <Tooltip
          key={role.name}
          title={
            role.description ? role.description : "No description provided"
          }
        >
          <Chip
            className={classes.chip}
            label={role.name}
            onDelete={() => handleRoleClick(role)}
          />
        </Tooltip>
      );
    });

    if (roleChips.length === 0) {
      return <Chip className={classes.chip} label="None" />;
    } else {
      return roleChips;
    }
  };

  renderRoleButton = () => {
    return (
      <Fab
        color="primary"
        variant="round"
        size="small"
        aria-label="Inherit Role"
        onClick={this.props.handleInheritRoleClick}
      >
        <Add />
      </Fab>
    );
  };

  render() {
    const { classes } = this.props;
    return (
      <div className={classes.bottomPad}>
        <Typography color="textSecondary">Roles:</Typography>
        <Divider />
        <div className={classes.topPad}>
          {this.renderRoleChips()}
          {this.renderRoleButton()}
        </div>
      </div>
    );
  }
}

RoleRow.propTypes = {
  classes: PropTypes.object.isRequired,
  handleInheritRoleClick: PropTypes.func.isRequired,
  selectedRoles: PropTypes.array.isRequired,
  handleRoleClick: PropTypes.func.isRequired,
};

const enhance = compose(withStyles(styles));

export default enhance(RoleRow);
