import { SplitButtonPassThroughOptions } from "primereact/splitbutton";

import { FindPropLabel } from "../passthrough/HelperPT";

export const SplitButtonPT = ({
  props,
}: {
  props: any;
}): SplitButtonPassThroughOptions => {
  return {
    menuButton: {
      root: {
        role: "img",
        "aria-label": `${FindPropLabel(props)}: Button Icon`,
      },
    },
  };
};
