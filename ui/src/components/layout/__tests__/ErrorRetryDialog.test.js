import React from 'react';
import { shallow } from 'enzyme';
import ErrorRetryDialog from '../ErrorRetryDialog';
import RetryTimer from '../RetryTimer';

const setup = propOverrides => {
  const props = Object.assign(
    {
      action: jest.fn(),
      error: { message: 'My Error Message' },
      loading: false,
    },
    propOverrides
  );

  const wrapper = shallow(<ErrorRetryDialog {...props} />);
  return {
    props,
    wrapper,
  };
};

describe('ErrorRetryDialog Component', () => {
  test('render', () => {
    const { wrapper } = setup();
    expect(wrapper.dive().find(RetryTimer)).toHaveLength(1);
  });
});
