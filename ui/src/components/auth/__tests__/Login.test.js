import React from 'react';
import Login from '../Login';
import { shallow } from 'enzyme';

describe('Login Component', () => {
  test('render', () => {
    const wrapper = shallow(<Login />);
    expect(wrapper.exists()).toBe(true);
  });
});
