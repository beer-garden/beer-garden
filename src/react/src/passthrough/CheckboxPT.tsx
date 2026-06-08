import { FindPropLabel } from "../passthrough/HelperPT";

export const CheckboxPT = ({ props }: { props: any }) => {
  return {
    input: {
      "aria-label": FindPropLabel(props),
    },
  };
};
