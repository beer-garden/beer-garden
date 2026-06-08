import { FindPropLabel } from "../passthrough/HelperPT";

export const ButtonPT = ({ props }: { props: any }) => {
  return {
    icon: {
      role: "img",
      "aria-label": `${FindPropLabel(props)}: Button Icon`,
    },
    root: {
      "aria-label": `${FindPropLabel(props)}: Button`,
    },
  };
};
