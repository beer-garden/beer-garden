import React from "react";
import { NavCrumbs } from "../NavCrumbs";
import { shallow } from "enzyme";
import Link from "@material-ui/core/Link";
import Typography from "@material-ui/core/Typography";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      pathname: "/foo/bar",
      mapping: {},
    },
    overrideProps,
  );

  const crumbs = shallow(<NavCrumbs {...props} />);

  return { crumbs, props };
};

describe("<NavCrumbs />", () => {
  describe("render", () => {
    it("should render a link for the non-current elements", () => {
      const { crumbs } = setup();
      expect(crumbs.find(Link)).toHaveLength(1);
      expect(crumbs.find(Link).prop("to")).toEqual("/foo");
    });

    it("should render a non-link for current elements", () => {
      const { crumbs } = setup();
      expect(crumbs.find(Typography)).toHaveLength(1);
      expect(
        crumbs.find(Typography).findWhere(node => node.key() === "/foo/bar"),
      ).toHaveLength(1);
    });

    it("should respect display values in mappings", () => {
      const { crumbs } = setup({ mapping: { bar: "BAR" } });
      const typo = crumbs.find(Typography);
      expect(typo.render().text()).toEqual("BAR");
    });
  });
});
