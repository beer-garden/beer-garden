import React from "react";
import { ListItem } from "@material-ui/core";
import { HelpfulLinks } from "../HelpfulLinks";
import { shallow } from "enzyme";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: { urlPrefix: "/" },
      config: {},
    },
    overrideProps,
  );
  const links = shallow(<HelpfulLinks {...props} />);
  return {
    links,
    props,
  };
};

describe("<HelpfulLinks />", () => {
  describe("render", () => {
    test("render no metrics url", () => {
      const { links } = setup();
      expect(links.find(ListItem)).toHaveLength(3);
    });

    test("render with metrics url", () => {
      const { links } = setup({ config: { metricsUrl: "/some/link" } });
      expect(links.find(ListItem)).toHaveLength(4);
    });
  });
});
