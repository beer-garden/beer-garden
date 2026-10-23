import { FindPropLabel } from "../passthrough/HelperPT";

export const InputTextPT = ({ props }: { props: any }) => {
  return {
    root: {
      autoComplete: "off",
      type:
        Object.hasOwn(props, "type") && props.type === "password"
          ? props.type
          : "text",
      "aria-label": FindPropLabel(props),
    },
  };
};
