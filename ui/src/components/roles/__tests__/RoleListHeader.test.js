import React from "react";
import { shallow } from "enzyme";
import { RoleListHeader } from "../RoleListHeader";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import TextField from "@material-ui/core/TextField";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      canAdd: true,
      addRoute: "/advanced/roles/add",
      filterText: "",
      onFilterChange: jest.fn(),
    },
    overrideProps,
  );
  const header = shallow(<RoleListHeader {...props} />);
  return {
    header,
    props,
  };
};

describe("<RoleListHeader />", () => {
  describe("render", () => {
    it("should render the title", () => {
      const { header } = setup();
      expect(header.find(Typography)).toHaveLength(1);
    });

    it("should render the button", () => {
      const { header } = setup();
      expect(header.find(Button)).toHaveLength(1);
    });

    it("should not render the button if the user cant see it", () => {
      const { header } = setup({ canAdd: false });
      expect(header.find(Button)).toHaveLength(0);
    });

    it("should render the search field", () => {
      const { header } = setup();
      expect(header.find(TextField)).toHaveLength(1);
    });
  });
});
