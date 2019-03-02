import React from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import PermissionList from "../roles/PermissionList";
import RoleRow from "../roles/RoleRow";

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

export function UserInfo(props) {
  const { classes, user } = props;
  return (
    <div className={classes.root}>
      <Typography gutterBottom variant="h5">
        Username: {user.username}
      </Typography>
      <RoleRow selectedRoles={user.roles} edit={false} />
      <PermissionList permissions={user.permissions} edit={false} />
    </div>
  );
}

UserInfo.propTypes = {
  classes: PropTypes.object.isRequired,
  user: PropTypes.object.isRequired,
};

const enhance = compose(withStyles(styles));

export default enhance(UserInfo);
