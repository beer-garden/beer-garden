import React from "react";
import { UsersRoot } from "../UsersRoot";
import { shallow } from "enzyme";
import AuthRoute from "../../auth/AuthRoute";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      match: { path: "/advanced/users" },
    },
    overrideProps,
  );

  const container = shallow(<UsersRoot {...props} />);
  return {
    container,
    props,
  };
};

describe("<UsersRoot />", () => {
  test("render routes", () => {
    const { container } = setup();
    expect(container.find(AuthRoute)).toHaveLength(3);
  });
});
