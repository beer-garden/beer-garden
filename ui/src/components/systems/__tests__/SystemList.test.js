import React from "react";
import { List, ListItem } from "@material-ui/core";
import { shallow } from "enzyme";
import { SystemList } from "../SystemList";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      systems: [{ id: 1, name: "system1", version: "1.0.0" }],
    },
    overrideProps,
  );
  const systemList = shallow(<SystemList {...props} />);
  return {
    systemList,
    props,
  };
};

describe("SystemList Component", () => {
  describe("render", () => {
    test("single system", () => {
      const { systemList } = setup();
      expect(systemList.find(List)).toHaveLength(1);
      expect(systemList.find(ListItem)).toHaveLength(1);
    });

    test("multiple systems", () => {
      const { systemList } = setup({
        systems: [
          { id: 1, name: "system1", version: "1.0.0" },
          { id: 2, name: "system2", version: "2.0.0" },
        ],
      });
      expect(systemList.find(List)).toHaveLength(1);
      expect(systemList.find(ListItem)).toHaveLength(2);
    });
  });
});
