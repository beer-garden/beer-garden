import React, { Component } from "react";
import PropTypes from "prop-types";
import {
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Typography,
  withStyles,
} from "@material-ui/core";
import { LeakAdd, BarChart, More } from "@material-ui/icons";

const styles = theme => ({
  root: {
    ...theme.mixins.gutters(),
    paddingTop: theme.spacing.unit * 2,
    paddingBottom: theme.spacing.unit * 2,
  },
});

export class HelpfulLinks extends Component {
  swaggerLink = () => {
    const {
      config: { urlPrefix, applicationName },
    } = this.props;
    return (
      <ListItem
        key="swaggerLink"
        button
        component="a"
        href={`${urlPrefix}swagger/index.html?config=${urlPrefix}config/swagger`}
      >
        <ListItemIcon>
          <LeakAdd color="secondary" fontSize="large" />
        </ListItemIcon>
        <ListItemText
          primary="Open API Documentation"
          secondary={`TODO: Make this link actually work. ${applicationName} uses OpenAPI to document our REST interface`}
        />
      </ListItem>
    );
  };

  metricsLink = () => {
    const {
      config: { metricsUrl },
    } = this.props;
    if (!metricsUrl) {
      return null;
    }
    return (
      <ListItem
        key="metricsLink"
        button
        component="a"
        target="_blank"
        href={`${metricsUrl}`}
      >
        <ListItemIcon>
          <BarChart color="secondary" fontSize="large" />
        </ListItemIcon>
        <ListItemText
          primary="Metrics"
          secondary="Check out Beer Garden and plugin metrics using Grafana!"
        />
      </ListItem>
    );
  };

  bgGrafanaLink = () => {
    return (
      <ListItem
        key="bgGrafanaLink"
        button
        component="a"
        target="_blank"
        href="https://grafana.com/dashboards/6621"
      >
        <ListItemIcon>
          <More color="secondary" fontSize="large" />
        </ListItemIcon>
        <ListItemText
          primary="Beer Garden Grafana Dashboard"
          secondary="A grafana dashboard you can download to monitor Beer Garden"
        />
      </ListItem>
    );
  };

  pluginGrafanaLink = () => {
    return (
      <ListItem
        key="pluginGrafanaLink"
        button
        component="a"
        target="_blank"
        href="https://grafana.com/dashboards/6624"
      >
        <ListItemIcon>
          <More color="secondary" fontSize="large" />
        </ListItemIcon>
        <ListItemText
          primary="Plugin Grafana Dashboard"
          secondary="A grafana dashboard you can download to monitor your plugins"
        />
      </ListItem>
    );
  };

  render() {
    const { classes } = this.props;

    return (
      <Paper className={classes.root}>
        <Typography variant="h4" gutterBottom>
          Helpful Links
        </Typography>
        <List>
          {this.swaggerLink()}
          {this.metricsLink()}
          {this.bgGrafanaLink()}
          {this.pluginGrafanaLink()}
        </List>
      </Paper>
    );
  }
}

HelpfulLinks.propTypes = {
  config: PropTypes.object.isRequired,
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(HelpfulLinks);
