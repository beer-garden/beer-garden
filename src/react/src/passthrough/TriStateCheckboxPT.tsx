import { FindPropLabel } from "../passthrough/HelperPT";

export const TriStateCheckboxPT = ({ props }: { props: any }) => {
  return {
    input: {
      "aria-label": FindPropLabel(props),
      "aria-checked": props.value === true ? "true" : "false",
    },
    box: {
      tabIndex: "-1",
      role: undefined,
      "aria-checked": undefined,
    },
  };
};
