import React from "react";
import { Switch, Route, MemoryRouter } from "react-router-dom";
import { mount } from "enzyme";
import { AuthRoute } from "../AuthRoute";

const TestLoginComponent = () => {
  return <h1>Test Login</h1>;
};

const TestComponent = () => {
  return <h1>Test</h1>;
};

const setup = propOverrides => {
  const props = Object.assign(
    {
      authEnabled: true,
      isAuthenticated: true,
      component: TestComponent,
    },
    propOverrides,
  );

  // We are not shallow mounting here because we want the router
  // to actually render the correct components.
  const route = mount(
    <MemoryRouter>
      <Switch>
        <Route exact path="/login" component={TestLoginComponent} />
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
  });
});
