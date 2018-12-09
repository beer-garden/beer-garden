import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import { Grid, Typography, Paper, Divider, Hidden } from '@material-ui/core';
import RetryTimer from './RetryTimer';

const styles = theme => ({
  paper: {
    padding: theme.spacing.unit * 2,
    textAlign: 'center',
  },
});

export class ErrorRetryDialog extends Component {
  render() {
    const { classes, action, error, loading } = this.props;

    return (
      <Grid container spacing={24}>
        <Hidden smDown>
          <Grid item xs />
        </Hidden>
        <Grid item xs={12} sm={6}>
          <Paper className={classes.paper}>
            <Typography variant="h2" gutterBottom color="error">
              Yikes! Something went wrong
            </Typography>
            <Typography gutterBottom variant="subtitle1">
              We're very sorry about that. It's likely that the API server is
              not responding. If this continues, please contact the
              administrator of your application.
            </Typography>
            <br />
            <Divider />
            <br />
            <Typography gutterBottom variant="subtitle2">
              In the meantime we will be retrying the connection to see if it
              comes back. There is nothing for you to do, but to watch the timer
              below.
            </Typography>
            <br />
            <Divider />
            <br />
            <RetryTimer action={action} error={error} loading={loading} />
          </Paper>
        </Grid>
        <Hidden smDown>
          <Grid item xs />
        </Hidden>
      </Grid>
    );
  }
}

ErrorRetryDialog.propTypes = {
  action: PropTypes.func.isRequired,
  error: PropTypes.object.isRequired,
  loading: PropTypes.bool.isRequired,
};

export default withStyles(styles)(ErrorRetryDialog);
