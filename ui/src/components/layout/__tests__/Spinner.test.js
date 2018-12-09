import React from 'react';
import Spinner from '../Spinner';
import { shallow } from 'enzyme';

describe('Spinner Component', () => {
  test('render', () => {
    const wrapper = shallow(<Spinner />);
    expect(wrapper.exists()).toBe(true);
  });
});
