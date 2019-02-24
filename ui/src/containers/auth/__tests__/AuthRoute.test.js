import React from "react";
import { Switch, Route, MemoryRouter } from "react-router-dom";
import { mount } from "enzyme";
import { AuthRoute } from "../AuthRoute";

const TestLoginComponent = () => {
  return <h1>Test Login</h1>;
};

const TestPWComponent = () => {
  return <h1>Test Password Change</h1>;
};

const TestComponent = () => {
  return <h1>Test</h1>;
};

const setup = propOverrides => {
  const props = Object.assign(
    {
      authEnabled: true,
      isAuthenticated: true,
      pwChangeRequired: false,
      component: TestComponent,
      render: null,
    },
    propOverrides,
  );

  // We are not shallow mounting here because we want the router
  // to actually render the correct components.
  const route = mount(
    <MemoryRouter>
      <Switch>
        <Route exact path="/login" component={TestLoginComponent} />
        <Route exact path="/user/settings" component={TestPWComponent} />
        <AuthRoute {...props} />
      </Switch>
    </MemoryRouter>,
  );
  return {
    props,
    route,
  };
};

describe("<AuthRoute />", () => {
  describe("render", () => {
    test("<TestLoginComponent />if auth is enabled and not authenticated", () => {
      const { route } = setup({ authEnabled: true, isAuthenticated: false });
      expect(route.find(TestLoginComponent)).toHaveLength(1);
    });

    test("<TestComponent /> if auth is disabled", () => {
      const { route } = setup({ authEnabled: false, isAuthenticated: false });
      expect(route.find(TestComponent)).toHaveLength(1);
    });

    test("<TestComponent /> if auth is enabled and authenticated", () => {
      const { route } = setup({ authEnabled: true, isAuthenticated: true });
      expect(route.find(TestComponent)).toHaveLength(1);
    });

    test("custom render function", () => {
      const route = mount(
        <MemoryRouter>
          <AuthRoute
            authEnabled
            isAuthenticated
            path="/"
            render={props => <TestComponent {...props} />}
          />
        </MemoryRouter>,
      );
      return expect(route.find(TestComponent)).toHaveLength(1);
    });

    it("should redirect to <TestPWComponent /> if pwChange is required", () => {
      const { route } = setup({
        authEnabled: true,
        isAuthenticated: true,
        pwChangeRequired: true,
      });
      expect(route.find(TestPWComponent)).toHaveLength(1);
    });
  });
});
