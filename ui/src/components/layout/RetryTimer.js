import React, { Component } from "react";
import PropTypes from "prop-types";
import { Typography, Tabs, Tab } from "@material-ui/core";
import Spinner from "./Spinner";

class RetryTimer extends Component {
  state = {
    timer: null,
    previousWaitTime: null,
    counter: 5,
    tabValue: 0,
  };

  componentDidMount() {
    let timer = setInterval(this.tick, 1000);
    this.setState({
      timer,
      counter: this.props.beginningWaitTime,
      previousWaitTime: this.props.beginningWaitTime,
    });
  }

  componentWillUnmount() {
    clearInterval(this.state.timer);
  }

  scaleCounter = () => {
    const { previousWaitTime } = this.state;
    const { scaleWait, maxWaitTime } = this.props;
    const newWaitTime = Math.min(previousWaitTime * scaleWait, maxWaitTime);
    this.setState({ previousWaitTime: newWaitTime });
    return newWaitTime;
  };

  tick = () => {
    const { loading } = this.props;
    if (loading) {
      return;
    }
    const { counter } = this.state;
    if (counter === 0) {
      this.props.action();
    }
    if (counter <= 0) {
      this.setState({ counter: this.scaleCounter() });
    } else {
      this.setState({
        counter: this.state.counter - 1,
      });
    }
  };

  handleTabChange = (event, value) => {
    this.setState({ tabValue: value });
  };

  getTimerItem = () => {
    let second;
    if (this.state.counter === 1) {
      second = "second";
    } else {
      second = "seconds";
    }
    return (
      <Typography variant="body1">
        Retrying in {this.state.counter} {second}...
      </Typography>
    );
  };

  getTabItem = () => {
    const { tabValue } = this.state;
    const { loading, error } = this.props;
    if (loading) {
      return <Spinner />;
    }

    if (tabValue === 0) {
      return this.getTimerItem();
    } else if (tabValue === 1) {
      return (
        <Typography variant="body1">Error Message: {error.message}.</Typography>
      );
    }
  };

  render() {
    const { tabValue } = this.state;
    return (
      <>
        <Tabs value={tabValue} onChange={this.handleTabChange} centered>
          <Tab label="Timer" />
          <Tab label="Details" />
        </Tabs>
        <br />
        {this.getTabItem()}
      </>
    );
  }
}

RetryTimer.propTypes = {
  maxWaitTime: PropTypes.number.isRequired,
  action: PropTypes.func.isRequired,
  beginningWaitTime: PropTypes.number.isRequired,
  scaleWait: PropTypes.number.isRequired,
  loading: PropTypes.bool.isRequired,
  error: PropTypes.object.isRequired,
};

RetryTimer.defaultProps = {
  maxWaitTime: 30,
  beginningWaitTime: 1,
  scaleWait: 2,
  loading: false,
};

export default RetryTimer;
