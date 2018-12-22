import React from "react";
import App from "../App";
import { shallow } from "enzyme";

describe("<App />", () => {
  test("render", () => {
    const wrapper = shallow(<App />);
    expect(wrapper.exists()).toBe(true);
  });
});
