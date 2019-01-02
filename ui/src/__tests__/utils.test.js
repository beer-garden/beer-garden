import { getCookie } from "../utils";

describe("getCookie", () => {
  test("match", () => {
    expect(getCookie("cookiename")).toEqual("cookievalue");
  });

  test("no match", () => {
    expect(getCookie("NOTTHERE")).toEqual(null);
  });
});
