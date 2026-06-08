import { FindPropLabel } from "../passthrough/HelperPT";

export const DialogPT = ({ props }: { props: any }) => {
  return {
    maximizableIcon: {
      role: "img",
      "aria-label": `${FindPropLabel(props)}: Maximizable`,
    },
  };
};
