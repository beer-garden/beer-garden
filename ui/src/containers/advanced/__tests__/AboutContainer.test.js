import React from "react";
import { AboutContainer } from "../AboutContainer";
import { shallow } from "enzyme";
import VersionInfo from "../../../components/advanced/VersionInfo";
import HelpfulLinks from "../../../components/advanced/HelpfulLinks";

const setup = propOverrides => {
  const props = Object.assign(
    {
      loadVersion: jest.fn(),
      version: {
        brewViewVersion: "3.0.0",
        bartenderVersion: "3.0.0",
        currentApiVersion: "v1",
        supportedApiVersions: ["v1"],
      },
      versionLoading: false,
      versionError: null,
      config: {},
    },
    propOverrides,
  );

  const container = shallow(<AboutContainer {...props} />);
  return {
    props,
    container,
  };
};

describe("<AboutContainer />", () => {
  describe("render", () => {
    test("version info and helpful links", () => {
      const { container } = setup();
      expect(container.find(VersionInfo)).toHaveLength(1);
      expect(container.find(HelpfulLinks)).toHaveLength(1);
    });
  });

  describe("componentDidMount", () => {
    test("it should call load version", () => {
      const { props } = setup();
      expect(props.loadVersion).toHaveBeenCalled();
    });
  });
});
