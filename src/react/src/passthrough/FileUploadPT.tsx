import { FindPropLabel } from "../passthrough/HelperPT";

export const FileUploadPT = ({ props }: { props: any }) => {
  return {
    root: {
      tabIndex: -1,
    },
    basicButton: {
      "aria-label": `${FindPropLabel(props)}: File Upload Bytes Choose Button`,
      role: "button",
    },
    chooseButton: {
      "aria-label": `${FindPropLabel(props)}: File Upload Base64 Choose Button`,
      role: "button",
    },
    chooseIcon: {
      role: "img",
      "aria-label": `${FindPropLabel(props)}: File Upload Base64 Choose Button Icon`,
    },
    actions: {
      "aria-description": `${FindPropLabel(props)}: File Upload Base64 Remove File Button, button is out of scope in framework to update accessibility labels`,
    },
  };
};
