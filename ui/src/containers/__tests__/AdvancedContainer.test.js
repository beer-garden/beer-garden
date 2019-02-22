import React from "react";
import { AdvancedContainer } from "../AdvancedContainer";
import { shallow } from "enzyme";
import AuthRoute from "../auth/AuthRoute";

const setup = overrideProps => {
  const props = Object.assign(
    {
      authEnabled: false,
      userData: {},
      classes: {},
      match: { path: "/advanced" },
      location: { pathname: "/advanced" },
    },
    overrideProps,
  );

  const container = shallow(<AdvancedContainer {...props} />);
  return {
    container,
    props,
  };
};

describe("<AdvancedContainer />", () => {
  test("render routes", () => {
    const { container } = setup();
    expect(container.find(AuthRoute)).toHaveLength(5);
  });
});
