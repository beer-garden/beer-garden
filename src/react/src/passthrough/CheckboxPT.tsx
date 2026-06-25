import { CheckboxPassThroughOptions } from "primereact/checkbox";

import { FindPropLabel } from "../passthrough/HelperPT";

export const CheckboxPT = ({
  props,
}: {
  props: any;
}): CheckboxPassThroughOptions => {
  return {
    input: {
      "aria-label": FindPropLabel(props),
    },
  };
};
