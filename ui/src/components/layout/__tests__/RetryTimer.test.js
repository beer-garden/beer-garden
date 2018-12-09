import React from 'react';
import Spinner from '../Spinner';
import RetryTimer from '../RetryTimer';
import { shallow } from 'enzyme';
import { Typography } from '@material-ui/core';

const setup = propOverrides => {
  const props = Object.assign(
    {
      maxWaitTime: 1,
      beginningWaitTime: 1,
      scaleWait: 1,
      loading: false,
      error: { message: 'Default Error Message' },
      action: jest.fn(),
    },
    propOverrides
  );
  jest.useFakeTimers();

  const wrapper = shallow(<RetryTimer {...props} />);
  return {
    props,
    wrapper,
  };
};

describe('RetryTimer Component', () => {
  test('render', () => {
    const { wrapper } = setup({});
    expect(wrapper.exists()).toBe(true);
  });

  test('Setup timer on init', () => {
    const { wrapper } = setup({ beginningWaitTime: 100 });
    const instance = wrapper.instance();
    instance.componentDidMount();
    expect(instance.state.counter).toBe(100);
    expect(instance.state.previousWaitTime).toBe(100);
    expect(instance.state.timer).not.toBeNull();
  });

  test('Destroy timer on unmount', () => {
    const { wrapper } = setup({ beginningWaitTime: 100 });
    const instance = wrapper.instance();
    instance.componentDidMount();
    instance.componentWillUnmount();
    expect(clearInterval).toHaveBeenCalled();
  });

  test('Display a spinner while loading', () => {
    const { wrapper } = setup({ loading: true });
    expect(wrapper.find(Spinner)).toHaveLength(1);
  });

  test('Display second(s) appropriately', () => {
    const { wrapper } = setup({ beginningWaitTime: 1 });
    let textElement = wrapper
      .find(Typography)
      .dive()
      .dive();
    expect(textElement.text()).toEqual('Retrying in 1 second...');
    wrapper.setState({ counter: 2 });
    textElement = wrapper
      .find(Typography)
      .dive()
      .dive();
    expect(textElement.text()).toEqual('Retrying in 2 seconds...');
  });

  test('Display the error message', () => {
    const { wrapper } = setup({ error: { message: 'foo' } });
    wrapper.setState({ tabValue: 1 });
    expect(
      wrapper
        .find(Typography)
        .dive()
        .dive()
        .text()
    ).toEqual('Error Message: foo.');
  });

  test('ticking moves counter appropriately', () => {
    const { wrapper } = setup({
      beginningWaitTime: 1,
      scaleWait: 2,
      maxWaitTime: 3,
    });
    const timer = wrapper.instance();
    expect(timer.state.counter).toBe(1);
    timer.tick();
    expect(timer.state.counter).toBe(0);
    timer.tick();
    expect(timer.state.counter).toBe(2);
    timer.tick();
    timer.tick();
    timer.tick();
    expect(timer.state.counter).toBe(3);
  });

  test('tick calls action when counter reaches 0', () => {
    const { wrapper, props } = setup({
      beginningWaitTime: 0,
    });
    const timer = wrapper.instance();
    timer.tick();
    expect(props.action).toHaveBeenCalled();
  });

  test('tick should do nothing if it is loading', () => {
    const { wrapper, props } = setup({
      beginningWaitTime: 0,
      loading: true,
    });
    const timer = wrapper.instance();
    timer.tick();
    expect(props.action).not.toHaveBeenCalled();
  });

  test('tab change', () => {
    const { wrapper } = setup();
    wrapper.instance().handleTabChange({}, 1);
    expect(wrapper.state('tabValue')).toBe(1);
  });
});
