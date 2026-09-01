import { FindPropLabel } from "../passthrough/HelperPT";

export const InputTextareaPT = ({ props }: { props: any }) => {
  return {
    root: {
      autoComplete: "off",
      "aria-label": FindPropLabel(props),
    },
  };
};
