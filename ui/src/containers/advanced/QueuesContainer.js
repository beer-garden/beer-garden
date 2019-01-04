import React, { Component } from "react";
import PropTypes from "prop-types";
import { Grid, Paper, Typography, withStyles } from "@material-ui/core";

const styles = theme => ({
  root: {
    ...theme.mixins.gutters(),
    paddingTop: theme.spacing.unit * 2,
    paddingBottom: theme.spacing.unit * 2,
  },
});

export class QueuesContainer extends Component {
  render() {
    const { classes } = this.props;
    return (
      <Grid container spacing={24}>
        <Grid item xs={12}>
          <Paper className={classes.root}>
            <Typography variant="h3">
              TODO: Render the Queues Container
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    );
  }
}

QueuesContainer.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(QueuesContainer);
