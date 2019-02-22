import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { Link as RouterLink } from "react-router-dom";
import { withStyles } from "@material-ui/core/styles";
import Link from "@material-ui/core/Link";
import Paper from "@material-ui/core/Paper";
import Typography from "@material-ui/core/Typography";
import Breadcrumbs from "@material-ui/lab/Breadcrumbs";
import NavigateNextIcon from "@material-ui/icons/NavigateNext";

const styles = theme => ({
  paper: {
    padding: `${theme.spacing.unit}px ${theme.spacing.unit * 2}px`,
    marginBottom: "10px",
  },
});

export class NavCrumbs extends Component {
  static propTypes = {
    classes: PropTypes.object.isRequired,
    pathname: PropTypes.string.isRequired,
    mapping: PropTypes.object,
  };

  render() {
    const { classes, pathname, mapping } = this.props;

    const pathnames = pathname.split("/").filter(r => r);

    const crumbs = [];
    let currentPath = [""];
    for (let i = 0; i < pathnames.length; i++) {
      const pathPart = pathnames[i];
      currentPath.push(pathPart);
      const to = currentPath.join("/");
      const display = pathPart in mapping ? mapping[pathPart] : pathPart;

      if (i === pathnames.length - 1) {
        crumbs.push(
          <Typography key={to} color="textPrimary">
            {display}
          </Typography>,
        );
      } else {
        crumbs.push(
          <Link key={to} component={RouterLink} color="inherit" to={to}>
            {display}
          </Link>,
        );
      }
    }

    return (
      <Paper className={classes.paper}>
        <Breadcrumbs
          separator={<NavigateNextIcon fontSize="small" />}
          aria-label="Breadcrumb"
        >
          {crumbs}
        </Breadcrumbs>
      </Paper>
    );
  }
}

const enhance = compose(withStyles(styles));

export default enhance(NavCrumbs);
