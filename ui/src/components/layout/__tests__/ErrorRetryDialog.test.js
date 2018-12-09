import React from 'react';
import { shallow } from 'enzyme';
import { ErrorRetryDialog } from '../ErrorRetryDialog';
import RetryTimer from '../RetryTimer';

const setup = propOverrides => {
  const props = Object.assign(
    {
      action: jest.fn(),
      error: { message: 'My Error Message' },
      loading: false,
      classes: { paper: 'paperClassName' },
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
    expect(wrapper.find(RetryTimer)).toHaveLength(1);
  });
});
