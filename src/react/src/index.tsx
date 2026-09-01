// import 'bootstrap/dist/css/bootstrap.min.css';
import { library } from "@fortawesome/fontawesome-svg-core";
import * as Icons from "@fortawesome/free-solid-svg-icons";
// Types
import {
  IconDefinition,
  IconPack,
  IconPrefix,
} from "@fortawesome/free-solid-svg-icons";
import React from "react";
import ReactDOM from "react-dom/client";

// import './index.css';
import App from "./App";
import reportWebVitals from "./reportWebVitals";

// Type that `library.add()` expects.
type IconDefinitionOrPack = IconDefinition | IconPack;

interface ImportedIcons {
  [key: string]: IconPrefix | IconDefinitionOrPack;
}

// Type `Icons` as a interface containing keys whose values are
// union of the resulting union type from above and `IconPrefix`.
const iconList = Object.keys(Icons)
  .filter((key) => key !== "fas" && key !== "prefix")
  .map((icon) => (Icons as ImportedIcons)[icon]);

library.add(...(iconList as IconDefinitionOrPack[]));

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement,
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
