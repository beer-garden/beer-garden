import React from 'react';
import { Root } from '../Root';
import { shallow } from 'enzyme';
import { Route } from 'react-router-dom';
import { CssBaseline } from '@material-ui/core';
import App from '../App';
import Login from '../../components/auth/Login';
import Spinner from '../../components/layout/Spinner';
import ErrorRetryDialog from '../../components/layout/ErrorRetryDialog';

const setup = propOverrides => {
  const props = Object.assign(
    {
      loadConfig: jest.fn(),
      config: { authEnabled: false },
      configLoading: false,
      configError: null,
    },
    propOverrides
  );

  const wrapper = shallow(<Root {...props} />);
  return {
    props,
    wrapper,
  };
};

describe('<Root />', () => {
  test('render', () => {
    const { wrapper } = setup();
    const divs = wrapper.find('div');
    expect(divs).toHaveLength(1);
    expect(wrapper.find(CssBaseline)).toHaveLength(1);
    const routes = wrapper.find(Route);
    expect(routes).toHaveLength(1);
    expect(routes.first().prop('component')).toEqual(App);
  });

  test('Render <Spinner /> while loading', () => {
    const { wrapper } = setup({ configLoading: true });
    expect(wrapper.find(Spinner)).toHaveLength(1);
  });

  test('render <ErrorRetryDialog/> if an error occurs', () => {
    const { wrapper } = setup({ configError: new Error('message') });
    expect(wrapper.find(ErrorRetryDialog)).toHaveLength(1);
  });

  test('render <ErrorRetryDialog /> if loading after an error', () => {
    const { wrapper } = setup({
      configLoading: true,
      configError: new Error('message'),
    });
    expect(wrapper.find(Spinner)).toHaveLength(0);
    expect(wrapper.find(ErrorRetryDialog)).toHaveLength(1);
  });

  test('render <Login /> if auth is enabled', () => {
    const { wrapper } = setup({ config: { authEnabled: true } });
    expect(wrapper.find(Spinner)).toHaveLength(0);
    expect(wrapper.find(ErrorRetryDialog)).toHaveLength(0);
    expect(wrapper.find('div')).toHaveLength(0);
    expect(wrapper.find(Login)).toHaveLength(1);
  });
});
