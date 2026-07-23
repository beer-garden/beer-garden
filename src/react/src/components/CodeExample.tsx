import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  Typography,
} from "@mui/material";

import { Request } from "../models/brewtils-types";
import { useSnackbar } from "../providers/SnackbarProvider";
import AccessButton from "./AccessButton";

function CodeExample({
  request,
  visibleCodeExample,
  setVisibleCodeExample,
}: {
  request: Request | undefined;
  visibleCodeExample: boolean;
  setVisibleCodeExample: (visibleCodeExample: boolean) => void;
}) {
  const showSnackbar = useSnackbar();

  const CodeBlock = (codeType: string) => {
    const getHostName = () => {
      return window.location.hostname;
    };

    const getPort = () => {
      return window.location.port;
    };

    const getPrefix = () => {
      const path = window.location.pathname;

      for (const knownPaths of ["/create", "/recreate"]) {
        const index = path.indexOf(knownPaths);
        if (index > 0) {
          return path.slice(1, index) + "/";
        }
      }

      return "";
    };

    const getSslEnabled = () => {
      return window.location.protocol === "https:" ? "True" : "False";
    };

    const wgetCode = () => {
      return `
      wget --method=POST -O- \\
        --body-data='${JSON.stringify(request)}' \\
        --header=Content-Type:application/json \\
        ${getHostName()}:${getPort()}${getPrefix()}/api/v1/requests?blocking=true
      `;
    };

    const curlCode = () => {
      return `
      curl -X POST ${getHostName()}:${getPort()}${getPrefix()}/api/v1/requests?blocking=true \\
        -H "Content-Type: application/json" \\
        -d '${JSON.stringify(request)}'
      `;
    };

    const pythonCode = () => {
      const generateParams = () => {
        if (request?.parameters) {
          const printParams = [] as Array<string>;

          for (const [key, value] of Object.entries(
            request?.parameters || {},
          )) {
            if (value && value !== undefined && value !== null) {
              if (typeof value === "string") {
                printParams.push(key + '="' + value + '"');
              } else if (typeof value === "boolean") {
                printParams.push(key + "=" + (value ? "True" : "False"));
              } else {
                printParams.push(key + "=" + value);
              }
            }
          }

          return printParams.join(", ");
        }
        return "";
      };

      return `
      from brewtils import SystemClient
      
      request = SystemClient(
        system_name = '${request?.system}',
        system_namespace = '${request?.namespace}',
        version_constraint = '${request?.system_version}',
        default_instance = '${request?.instance_name}',
        bg_host = '${getHostName()}',
        bg_url_prefix = '${getPrefix()}',
        bg_port = ${getPort()},
        blocking = True,
        ssl_enabled = ${getSslEnabled()},
        ca_cert = None,
        ca_verify = None,
        client_cert = None).${request?.command ? request?.command : "command"}(${generateParams()})
      
      print(request)
      `;
    };

    const code = () => {
      if (codeType === "Python") {
        return pythonCode();
      }
      if (codeType === "cURL") {
        return curlCode();
      }
      if (codeType === "Wget") {
        return wgetCode();
      }

      if (codeType === "JSON") {
        return JSON.stringify(request, null, 2);
      }

      return "";
    };
    const copyToClipboard = () => {
      navigator.clipboard.writeText(code()).catch((error) => {
        console.error("Error copying to clipboard:", error);
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error copying to clipboard: ${error}`,
          life: 3000,
        });
      });
    };

    return (
      <Box sx={{ position: "relative", mb: 2 }}>
        <Typography variant="h6">{codeType}</Typography>
        <AccessButton
          className="p-button-rounded p-button-text"
          onClick={copyToClipboard}
          style={{ position: "absolute", top: "0.5rem", right: "0.5rem" }}
          tooltip={`Copy ${codeType} to clipboard`}
        >
          <FontAwesomeIcon icon="copy" />
        </AccessButton>
        <pre>
          <code
            style={{
              whiteSpace: "pre-wrap",
              overflowWrap: "break-word",
              overflowX: "auto",
            }}
          >
            {code()}
          </code>
        </pre>
      </Box>
    );
  };

  return (
    <Dialog
      open={visibleCodeExample}
      onClose={() => {
        if (!visibleCodeExample) return;
        setVisibleCodeExample(false);
      }}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle sx={{ m: 0, p: 2 }} id="customized-dialog-title">
        <Grid container>
          <Grid size="grow">Code Examples</Grid>
          <Grid>
            <AccessButton
              sx={{ mr: 2 }}
              onClick={() => {
                setVisibleCodeExample(false);
              }}
            >
              <FontAwesomeIcon icon="xmark" />
            </AccessButton>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" sx={{ mb: 2 }}>
          Bytes and Base64 parameters are not supported in code examples.
        </Typography>
        {CodeBlock("Python")}

        {CodeBlock("cURL")}

        {CodeBlock("Wget")}

        {CodeBlock("JSON")}
      </DialogContent>
    </Dialog>
  );
}

export default CodeExample;
