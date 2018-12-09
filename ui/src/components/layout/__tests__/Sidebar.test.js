import React from 'react';
import { shallow } from 'enzyme';
import { Drawer } from '@material-ui/core';
import Sidebar from '../Sidebar';

describe('Sidebar Component', () => {
  test('render', () => {
    const wrapper = shallow(<Sidebar />);
    expect(wrapper.dive().find(Drawer)).toHaveLength(1);
  });
});
