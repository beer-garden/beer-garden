import { FindPropLabel } from "../passthrough/HelperPT";

export const SplitButtonPT = ({ props }: { props: any }) => {
  return {
    menuButton: {
      role: "img",
      "aria-label": `${FindPropLabel(props)}: Button Icon`,
    },
  };
};
