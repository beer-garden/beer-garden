import React from "react";
import { Redirect } from "react-router-dom";
import { UserSettingsContainer } from "../UserSettingsContainer";
import { shallow } from "enzyme";
import { flushPromises } from "../../../testHelpers";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import UserForm from "../../../components/users/UserForm";

const setup = (overrideProps, overrideState) => {
  const props = Object.assign(
    {
      classes: {},
      currentUser: { username: "user1", sub: "userId" },
      updateUserError: null,
      updateUserLoading: false,
      updateUser: jest.fn().mockResolvedValue({}),
      pwChangeRequired: false,
    },
    overrideProps,
  );

  const initialState = Object.assign(
    {
      username: { value: "name", error: false, help: "" },
      currentPassword: { value: "prevPassword", error: false, help: "" },
      password: { value: "!QAZ2wsx", error: false, help: "" },
      confirmPassword: { value: "!QAZ2wsx", error: false, help: "" },
    },
    overrideState,
  );

  const container = shallow(<UserSettingsContainer {...props} />);
  container.setState(initialState);
  return {
    container,
    props,
  };
};

describe("<UsersSettingsContainer />", () => {
  describe("handleFormChange", () => {
    it("should actually update the state correctly.", () => {
      const { container } = setup();
      container.setState({
        username: { value: "nam", error: true, help: "help message" },
      });
      const event = { target: { name: "username", value: "name" } };
      container.instance().handleFormChange(event);
      expect(container.state().username.value).toEqual("name");
      expect(container.state().username.help).toEqual("");
      expect(container.state().username.error).toBe(false);
    });
  });

  describe("handleSubmit", () => {
    it("should call updateUser correctly", async () => {
      const {
        container,
        props: { updateUser },
      } = setup();

      container.instance().handleSubmit({ preventDefault: () => {} });
      await flushPromises();
      expect(updateUser).toHaveBeenCalled();
      expect(updateUser).toHaveBeenCalledWith(
        { username: "user1", id: "userId" },
        {
          username: "user1",
          password: "!QAZ2wsx",
          currentPassword: "prevPassword",
        },
      );
    });

    it("should update the successMessage on success", async () => {
      const { container } = setup();

      container.instance().handleSubmit({ preventDefault: () => {} });
      await flushPromises();
      expect(container.state().successMessage).toEqual(
        "Successfully updated password",
      );
    });

    it("should not update the user if the form is not valid", async () => {
      const {
        container,
        props: { updateUser },
      } = setup({}, { password: "" });
      container.instance().handleSubmit({ preventDefault: () => {} });
      await flushPromises();
      expect(updateUser).not.toHaveBeenCalled();
    });

    it("should redirect on success and pwChangeRequired is true", async () => {
      const { container } = setup({ pwChangeRequired: true });
      container.instance().handleSubmit({ preventDefault: () => {} });
      await flushPromises();
      expect(container.state().redirect).toBe(true);
    });
  });

  describe("validatePassword", () => {
    it("should check that the text fields are required", () => {
      const { container } = setup(
        {},
        {
          currentPassword: { value: "", error: false, help: "" },
          password: { value: "", error: false, help: "" },
          confirmPassword: { value: "", error: false, help: "" },
        },
      );
      const valid = container.instance().validatePassword();
      expect(valid).toBe(false);
      expect(container.state().currentPassword.error).toBe(true);
      expect(container.state().password.error).toBe(true);
      expect(container.state().confirmPassword.error).toBe(true);
    });

    it("should validate that the passwords match", () => {
      const { container } = setup(
        {},
        {
          password: { value: "asdf", error: false, help: "" },
          confirmPassword: { value: "qwer", error: false, help: "" },
        },
      );
      const valid = container.instance().validatePassword();
      expect(valid).toBe(false);
      expect(container.state().password.error).toBe(true);
      expect(container.state().confirmPassword.error).toBe(true);
      expect(container.state().password.help).toEqual("Passwords do not match");
    });
  });

  describe("render", () => {
    it("should render the important bits", () => {
      const { container } = setup();
      expect(container.find(Button)).toHaveLength(1);
      expect(container.find(Typography)).toHaveLength(3);
      expect(container.find(UserForm)).toHaveLength(1);
    });

    it("should render an extra Typography if pwChangeRequired", () => {
      const { container } = setup({ pwChangeRequired: true });
      expect(container.find(Typography)).toHaveLength(4);
    });

    it("should redirect if redirect is true", () => {
      const { container } = setup({}, { redirect: true });
      expect(container.find(Redirect)).toHaveLength(1);
    });
  });
});
