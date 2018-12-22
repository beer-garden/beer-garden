import React, { Component } from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import { Typography, withStyles } from "@material-ui/core";
import Topbar from "../components/layout/Topbar";
import Sidebar from "../components/layout/Sidebar";
import SystemList from "../components/systems/SystemList";
import { fetchSystems } from "../actions/system";
import Spinner from "../components/layout/Spinner";

const styles = theme => {
  console.log(theme.mixins.toolbar);
  return {
    content: {
      flexGrow: 1,
      padding: theme.spacing.unit * 2,
    },
    topbarSpacer: theme.mixins.toolbar,
  };
};

class Dashboard extends Component {
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

Dashboard.propTypes = {
  classes: PropTypes.object.isRequired,
  systems: PropTypes.array.isRequired,
  systemsLoading: PropTypes.bool.isRequired,
  systemsError: PropTypes.object,
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
)(withStyles(styles)(Dashboard));
