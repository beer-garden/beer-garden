import React from "react";
import { SystemDashboard } from "../SystemDashboard";
import { shallow } from "enzyme";
import SystemList from "../../components/systems/SystemList";
import Spinner from "../../components/layout/Spinner";
import Sidebar from "../../components/layout/Sidebar";

const setup = propOverrides => {
  const props = Object.assign(
    {
      classes: { topbarSpacer: "topbarSpacer" },
      systems: [{ id: 1, name: "system1", version: "1.0.0" }],
      systemsLoading: false,
      systemsError: null,
      fetchSystems: jest.fn(),
    },
    propOverrides,
  );

  const dashboard = shallow(<SystemDashboard {...props} />);
  return {
    props,
    dashboard,
  };
};

describe("<SystemDashboard/>", () => {
  describe("render", () => {
    test("spacer should exist", () => {
      const { dashboard } = setup();
      expect(dashboard.find("div").hasClass("topbarSpacer")).toBe(true);
    });

    test("loading", () => {
      const { dashboard } = setup({ systemsLoading: true });
      expect(dashboard.find(Spinner)).toHaveLength(1);
    });

    test("sidebar and systems", () => {
      const { dashboard } = setup();
      expect(dashboard.find(Sidebar)).toHaveLength(1);
      expect(dashboard.find(SystemList)).toHaveLength(1);
    });
  });
});
