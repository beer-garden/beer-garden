import React from "react";
import { SystemsContainer } from "../SystemsContainer";
import { shallow } from "enzyme";
import SystemList from "../../components/systems/SystemList";
import Spinner from "../../components/layout/Spinner";

const setup = propOverrides => {
  const props = Object.assign(
    {
      systems: [{ id: 1, name: "system1", version: "1.0.0" }],
      systemsLoading: false,
      systemsError: null,
      fetchSystems: jest.fn(),
    },
    propOverrides,
  );

  const container = shallow(<SystemsContainer {...props} />);
  return {
    props,
    container,
  };
};

describe("<SystemsContainer/>", () => {
  describe("render", () => {
    test("loading", () => {
      const { container } = setup({ systemsLoading: true });
      expect(container.find(Spinner)).toHaveLength(1);
    });

    test("systems", () => {
      const { container } = setup();
      expect(container.find(SystemList)).toHaveLength(1);
    });
  });
});
