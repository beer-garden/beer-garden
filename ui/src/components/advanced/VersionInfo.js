import React, { Component } from "react";
import PropTypes from "prop-types";
import {
  Chip,
  Paper,
  Typography,
  Table,
  TableHead,
  TableRow,
  TableCell,
  withStyles,
} from "@material-ui/core";
import green from "@material-ui/core/colors/green";
import Spinner from "../layout/Spinner";

const styles = theme => ({
  root: {
    ...theme.mixins.gutters(),
    paddingTop: theme.spacing.unit * 2,
    paddingBottom: theme.spacing.unit * 2,
  },
  success: {
    color: "white",
    backgroundColor: green[600],
  },
  error: {
    color: "white",
    backgroundColor: theme.palette.error.dark,
  },
});

export class VersionInfo extends Component {
  getStatusChip = (version, classes) => {
    if (version === "unknown") {
      return <Chip label="Unavailable" className={classes.error} />;
    } else {
      return <Chip label="Running" className={classes.success} />;
    }
  };

  getVersionTable = (version, classes) => {
    return (
      <Table>
        <TableHead>
          <TableRow>
            <TableCell align="left">Component Name</TableCell>
            <TableCell align="center">Status</TableCell>
            <TableCell align="right">Component Version</TableCell>
          </TableRow>
          <TableRow>
            <TableCell align="left">Brew View</TableCell>
            <TableCell align="center">
              {this.getStatusChip(version.brewViewVersion, classes)}
            </TableCell>
            <TableCell align="right">{version.brewViewVersion}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell align="left">Bartender</TableCell>
            <TableCell align="center">
              {this.getStatusChip(version.bartenderVersion, classes)}
            </TableCell>
            <TableCell align="right">{version.bartenderVersion}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell align="left">Current API</TableCell>
            <TableCell align="center" />
            <TableCell align="right">{version.currentApiVersion}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell align="left">Supported API Versions</TableCell>
            <TableCell align="center" />
            <TableCell align="right">
              {version.supportedApiVersions.join(", ")}
            </TableCell>
          </TableRow>
        </TableHead>
      </Table>
    );
  };
  render() {
    const { loading, version, error, classes } = this.props;
    let versionElement;
    if (loading) {
      versionElement = <Spinner />;
    } else if (error !== null) {
      versionElement = (
        <Typography id="versionError" variant="body1" color="error">
          {error.message}
        </Typography>
      );
    } else {
      versionElement = this.getVersionTable(version, classes);
    }

    return (
      <Paper className={classes.root}>
        <Typography variant="h4" gutterBottom>
          Version Information
        </Typography>
        {versionElement}
      </Paper>
    );
  }
}

VersionInfo.propTypes = {
  loading: PropTypes.bool.isRequired,
  version: PropTypes.object.isRequired,
  classes: PropTypes.object.isRequired,
  error: PropTypes.object,
};

export default withStyles(styles)(VersionInfo);
