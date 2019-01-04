import React from "react";
import { Table, Chip } from "@material-ui/core";
import Spinner from "../../../components/layout/Spinner";
import { VersionInfo } from "../VersionInfo";
import { shallow } from "enzyme";

const setup = overrideProps => {
  const props = Object.assign(
    {
      loading: false,
      version: {
        brewViewVersion: "3.0.0",
        bartenderVersion: "3.0.0",
        currentApiVersion: "v1",
        supportedApiVersions: ["v1"],
      },
      error: null,
      classes: {},
    },
    overrideProps,
  );
  const versionInfo = shallow(<VersionInfo {...props} />);
  return {
    versionInfo,
    props,
  };
};

describe("<VersionInfo />", () => {
  describe("render", () => {
    test("loading", () => {
      const { versionInfo } = setup({ loading: true });
      expect(versionInfo.find(Spinner)).toHaveLength(1);
    });

    test("if error occurred", () => {
      const { versionInfo } = setup({ error: new Error("error message") });
      const errorElement = versionInfo.find("#versionError");
      expect(errorElement).toHaveLength(1);
    });

    test("all success", () => {
      const { versionInfo } = setup();
      expect(versionInfo.find(Table)).toHaveLength(1);
    });

    test("check chips", () => {
      const { versionInfo } = setup({
        version: {
          bartenderVersion: "unknown",
          brewViewVersion: "unknown",
          supportedApiVersions: ["v1"],
          currentApiVerison: "v1",
        },
      });
      const chips = versionInfo.find(Chip);
      expect(chips).toHaveLength(2);
      expect(chips.first().prop("label")).toEqual("Unavailable");
    });
  });
});
