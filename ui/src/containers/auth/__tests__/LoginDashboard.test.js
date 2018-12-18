import React from 'react';
import { Redirect } from 'react-router-dom';
import { Grid } from '@material-ui/core';
import { shallow } from 'enzyme';
import Login from '../../../components/auth/Login';
import Topbar from '../../../components/layout/Topbar';
import { LoginDashboard } from '../LoginDashboard';

const setup = propOverrides => {
  const props = Object.assign(
    {
      classes: {},
      config: { authEnabled: true, guestLoginEnabled: true },
      auth: { isAuthenticated: false },
      basicLogin: jest.fn(),
    },
    propOverrides,
  );

  const dashboard = shallow(<LoginDashboard {...props} />);
  return {
    props,
    dashboard,
  };
};
describe('<LoginDashboard />', () => {
  describe('render', () => {
    test('redirect if authentication is not required', () => {
      const { dashboard } = setup({ auth: { isAuthenticated: true } });
      expect(dashboard.find(Redirect)).toHaveLength(1);
    });

    test('login, topbar and grid', () => {
      const { dashboard } = setup();
      expect(dashboard.find(Topbar)).toHaveLength(1);
      expect(dashboard.find(Login)).toHaveLength(1);
      expect(dashboard.find(Grid)).toHaveLength(3);
    });
  });
});
