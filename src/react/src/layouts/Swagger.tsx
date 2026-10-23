import "swagger-ui-react/swagger-ui.css";

import SwaggerUI from "swagger-ui-react";

import { GetBaseURL } from "../services/util_service";

function Swagger() {
  return (
    <div className="p-4">
      <SwaggerUI url={`${GetBaseURL()}/api/v1/spec`} />
    </div>
  );
}

export default Swagger;
