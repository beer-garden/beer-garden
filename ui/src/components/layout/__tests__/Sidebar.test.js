import React from 'react';
import { shallow } from 'enzyme';
import { Drawer } from '@material-ui/core';
import { Sidebar } from '../Sidebar';

describe('Sidebar Component', () => {
  test('render', () => {
    const props = { classes: { drawer: 'drawerClass' } };
    const wrapper = shallow(<Sidebar {...props} />);
    expect(wrapper.find(Drawer)).toHaveLength(1);
  });
});
