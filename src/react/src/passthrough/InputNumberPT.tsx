import { FindPropLabel } from "../passthrough/HelperPT";

export const InputNumberPT = ({ props }: { props: any }) => {
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
