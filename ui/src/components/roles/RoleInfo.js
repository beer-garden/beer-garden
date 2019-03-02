import React from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import PermissionList from "./PermissionList";

const styles = theme => ({
  root: {
    paddingTop: theme.spacing.unit * 2,
    paddingBottom: theme.spacing.unit * 2,
  },
  chip: {
    marginRight: theme.spacing.unit,
  },
  topPad: {
    paddingTop: theme.spacing.unit,
  },
});

export function RoleInfo(props) {
  const { classes, role } = props;
  return (
    <div className={classes.root}>
      <Typography gutterBottom variant="h5" inline>
        {role.name} -{" "}
      </Typography>
      <Typography gutterBottom variant="subtitle1" inline>
        {role.description}
      </Typography>
      <PermissionList permissions={role.permissions} edit={false} />
    </div>
  );
}

RoleInfo.propTypes = {
  classes: PropTypes.object.isRequired,
  role: PropTypes.object.isRequired,
};

const enhance = compose(withStyles(styles));

export default enhance(RoleInfo);
