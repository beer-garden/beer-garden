import { InputNumberPassThroughOptions } from "primereact/inputnumber";

import { FindPropLabel } from "../passthrough/HelperPT";

export const InputNumberPT = ({
  props,
}: {
  props: any;
}): InputNumberPassThroughOptions => {
  return {
    input: {
      root: {
        autoComplete: "off",
        "aria-label": FindPropLabel(props),
        "aria-valuenow": `${
          props.value !== null && props.value !== undefined
            ? JSON.stringify(props.value)
            : "0"
        }`,
      },
    },
  };
};
