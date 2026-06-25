import { InputTextPassThroughOptions } from "primereact/inputtext";

import { FindPropLabel } from "../passthrough/HelperPT";

export const InputTextareaPT = ({
  props,
}: {
  props: any;
}): InputTextPassThroughOptions => {
  return {
    root: {
      autoComplete: "off",
      "aria-label": FindPropLabel(props),
    },
  };
};
