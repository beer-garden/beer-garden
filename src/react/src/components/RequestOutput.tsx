import { Button } from "primereact/button";
import { Skeleton } from "primereact/skeleton";
import { useState } from "react";

import { Request } from "../models/brewtils-types";

function largeOutputCheck(request: Request): boolean {
  if (request.output_type === "JSON") {
    try {
      if (Object.keys(JSON.parse(request.output || "{}")).length > 1000) {
        return false;
      }
    } catch {
      // Pass
    }
  }
  if (new Blob([request.output ?? ""]).size > 5000000) {
    return false;
  }

  return true;
}

function formattedOutputData(request: Request) {
  if (request.output_type === "JSON") {
    let parsed_output = {};
    try {
      parsed_output = JSON.parse(request.output || "{}");
    } catch {
      parsed_output = { error: "Failed to parse JSON output" };
    }

    return (
      <pre
        style={{
          whiteSpace: "pre-wrap",
          overflowWrap: "break-word",
          overflowX: "auto",
        }}
      >
        {JSON.stringify(parsed_output, null, 2)}
      </pre>
    );
  }

  if (request.output_type === "HTML") {
    return (
      <div dangerouslySetInnerHTML={{ __html: request.output || "" }}></div>
    );
  }

  // Covers STRING, XML, JS, CSS
  return (
    <pre
      style={{
        whiteSpace: "pre-wrap",
        overflowWrap: "break-word",
        overflowX: "auto",
      }}
    >
      {request.output}
    </pre>
  );
}

function displayOutput(request: Request) {
  const [showOutput, setShowOutput] = useState(largeOutputCheck(request));

  return (
    <div>
      {!showOutput && (
        <div>
          <div>Output is too large</div>
          <Button
            label="Show Output"
            severity="warning"
            icon="pi pi-arrow-right"
            iconPos="right"
            data-testid="request-show-output"
            onClick={() => setShowOutput(true)}
          />
        </div>
      )}
      {showOutput && formattedOutputData(request)}
    </div>
  );
}

function RequestOutput(request: Request) {
  if (
    request.status &&
    ["CREATED", "RECEIVED", "IN_PROGRESS"].includes(request.status)
  ) {
    return (
      <div id="request-output-skeleton">
        <Skeleton width="100%" height="200px" borderRadius="16px" />
      </div>
    );
  }

  return <div id="request-output">{displayOutput(request)}</div>;
}

export default RequestOutput;
