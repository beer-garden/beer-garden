import { configure } from "enzyme";
import Adapter from "enzyme-adapter-react-16";
import "jest-localstorage-mock";

configure({ adapter: new Adapter() });
