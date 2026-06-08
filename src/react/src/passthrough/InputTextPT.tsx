import { FindPropLabel } from "../passthrough/HelperPT";

export const InputTextPT = ({ props }: { props: any }) => {
  return {
    root: {
      autoComplete: "off",
      type: "text",
      "aria-label": FindPropLabel(props),
    },
  };
};
