import React from "react";
import PropTypes from "prop-types";
import { withStyles } from "@material-ui/core/styles";
import CircularProgress from "@material-ui/core/CircularProgress";

const styles = theme => ({
  progress: {
    margin: theme.spacing.unit * 2,
  },
});

export function Spinner(props) {
  const { classes, color, size } = props;
  return (
    <CircularProgress className={classes.progress} color={color} size={size} />
  );
}

Spinner.propTypes = {
  classes: PropTypes.object.isRequired,
  color: PropTypes.string.isRequired,
  size: PropTypes.number.isRequired,
};

Spinner.defaultProps = {
  color: "primary",
  size: 40,
};

export default withStyles(styles)(Spinner);
