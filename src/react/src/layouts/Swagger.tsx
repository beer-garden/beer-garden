import "swagger-ui-react/swagger-ui.css";

import { Box } from "@mui/material";
import SwaggerUI from "swagger-ui-react";

import { GetBaseURL } from "../services/util_service";

function Swagger() {
  return (
    <Box sx={{ p: 2 }}>
      <SwaggerUI url={`${GetBaseURL()}/api/v1/spec`} />
    </Box>
  );
}

export default Swagger;
