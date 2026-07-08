import { FindPropLabel } from "../passthrough/HelperPT";

export const CalendarPT = ({ props }: { props: any }) => {
  return {
    input: {
      root: ({ context }: { context: any }) => {
        if (!context.disabled) {
          return {
            "aria-label": FindPropLabel(props),
            "aria-controls": undefined,
            "aria-description":
              "Select Date and Time, aria-controls removed when popup is not in DOM",
          };
        }
        return {
          "aria-label": FindPropLabel(props),
          "aria-description": "Select Date and Time",
        };
      },
    },
  };
};
