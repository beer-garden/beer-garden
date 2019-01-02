import { configure } from "enzyme";
import Adapter from "enzyme-adapter-react-16";
import "jest-localstorage-mock";

configure({ adapter: new Adapter() });

Object.defineProperty(window.document, "cookie", {
  writable: true,
  value: "cookiename=cookievalue",
  match: String.match,
});
