import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { connect } from "react-redux";
import Spinner from "../components/layout/Spinner";
import SystemList from "../components/systems/SystemList";
import { fetchSystems } from "../actions/system";

export class SystemsContainer extends Component {
  componentDidMount() {
    this.props.fetchSystems();
  }

  render() {
    const { systemsLoading, systems } = this.props;
    if (systemsLoading) {
      return <Spinner />;
    }

    return <SystemList systems={systems} />;
  }
}

SystemsContainer.propTypes = {
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

const enhance = compose(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  ),
);

export default enhance(SystemsContainer);
