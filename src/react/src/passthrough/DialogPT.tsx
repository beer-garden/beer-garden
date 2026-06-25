import { DialogPassThroughOptions } from "primereact/dialog";

import { FindPropLabel } from "../passthrough/HelperPT";

export const DialogPT = ({
  props,
}: {
  props: any;
}): DialogPassThroughOptions => {
  return {
    maximizableIcon: {
      role: "img",
      "aria-label": `${FindPropLabel(props)}: Maximizable`,
    },
  };
};
