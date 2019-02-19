import React from "react";
import { shallow } from "enzyme";
import { UserForm } from "../UserForm";
import Input from "@material-ui/core/Input";

const setup = overrideProps => {
  const props = Object.assign(
    {
      classes: {},
      username: { value: "", error: false, help: "" },
      handleFormChange: jest.fn(),
      password: { value: "", error: false, help: "" },
      confirmPassword: { value: "", error: false, help: "" },
    },
    overrideProps,
  );
  const form = shallow(<UserForm {...props} />);
  return {
    form,
    props,
  };
};

describe("<UserForm />", () => {
  describe("render", () => {
    it("should render inputs", () => {
      const { form } = setup();
      expect(form.find(Input)).toHaveLength(3);
    });

    it("should render an extra input if currentPassword is provided", () => {
      const { form } = setup({
        currentPassword: { value: "", error: false, help: "" },
      });
      expect(form.find(Input)).toHaveLength(4);
    });
  });
});
