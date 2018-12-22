import React, { Component } from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import { withStyles } from "@material-ui/core";
import Sidebar from "../components/layout/Sidebar";
import SystemList from "../components/systems/SystemList";
import { fetchSystems } from "../actions/system";
import Spinner from "../components/layout/Spinner";

const styles = theme => {
  return {
    content: {
      flexGrow: 1,
      padding: theme.spacing.unit * 2,
    },
    topbarSpacer: theme.mixins.toolbar,
  };
};

export class SystemDashboard extends Component {
  componentDidMount() {
    this.props.fetchSystems();
  }

  render() {
    const { classes, systemsLoading, systems } = this.props;
    if (systemsLoading) {
      return (
        <>
          <main className={classes.content}>
            <div className={classes.topbarSpacer} />
            <Spinner />
          </main>
        </>
      );
    }

    return (
      <>
        <Sidebar />
        <main className={classes.content}>
          <div className={classes.topbarSpacer} />
          {<SystemList systems={systems} />}
        </main>
      </>
    );
  }
}

SystemDashboard.propTypes = {
  classes: PropTypes.object.isRequired,
  systems: PropTypes.array.isRequired,
  systemsLoading: PropTypes.bool.isRequired,
  systemsError: PropTypes.object,
  fetchSystems: PropTypes.func.isRequired,
};

const mapStateToProps = state => {
  return {
    systems: state.systemReducer.systems,
    systemsLoading: state.systemReducer.systemsLoading,
    systemsError: state.systemReducer.systemsError,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    fetchSystems: () => dispatch(fetchSystems()),
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps,
)(withStyles(styles)(SystemDashboard));
