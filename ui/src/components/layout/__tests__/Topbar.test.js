import React from 'react';
import { shallow } from 'enzyme';
import { AppBar, IconButton } from '@material-ui/core';
import Topbar from '../Topbar';

describe('Topbar Component', () => {
  test('render', () => {
    const wrapper = shallow(<Topbar />);
    expect(wrapper.dive().find(AppBar)).toHaveLength(1);
  });

  test('Toggle user settings', () => {
    const wrapper = shallow(<Topbar />).dive();
    expect(wrapper.state('anchorEl')).toBeNull();
    wrapper.find(IconButton).simulate('click', { currentTarget: 'target' });
    expect(wrapper.state('anchorEl')).toEqual('target');
  });
});
