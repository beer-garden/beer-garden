import React from 'react';
import { shallow } from 'enzyme';
import { AppBar, IconButton } from '@material-ui/core';
import { Topbar } from '../Topbar';

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: { appBar: 'appBarClassName' },
      config: { applicationName: 'Beer Garden' },
      auth: { isAuthenticated: true },
    },
    overrideProps,
  );
  const wrapper = shallow(<Topbar {...props} />);
  return {
    wrapper,
    props,
  };
};

describe('Topbar Component', () => {
  test('render', () => {
    const { wrapper } = setup();
    expect(wrapper.find(AppBar)).toHaveLength(1);
  });

  test('Toggle user settings', () => {
    const { wrapper } = setup();
    expect(wrapper.state('anchorEl')).toBeNull();
    wrapper.find(IconButton).simulate('click', { currentTarget: 'target' });
    expect(wrapper.state('anchorEl')).toEqual('target');
    wrapper.instance().handleClose();
    expect(wrapper.state('anchorEl')).toBeNull();
  });
});
