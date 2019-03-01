import React from "react";
import { RolesRoot } from "../RolesRoot";
import { shallow } from "enzyme";
import AuthRoute from "../../auth/AuthRoute";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      match: { path: "/advanced/roles" },
    },
    overrideProps,
  );

  const container = shallow(<RolesRoot {...props} />);
  return {
    container,
    props,
  };
};

describe("<RolesRoot />", () => {
  test("render routes", () => {
    const { container } = setup();
    expect(container.find(AuthRoute)).toHaveLength(3);
  });
});
