import { Panel } from "primereact/panel";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Config, Version } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetVersion } from "../services/util_service";

function AboutIndex({ config }: { config: Config }) {
  const [version, setVersion] = useState<Version | null>(null);
  const showSnackbar = useSnackbar();

  useEffect(() => {
    GetVersion()
      .then((version) => {
        setVersion(version);
      })
      .catch((error) => {
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error fetching the version: ${error}`,
          life: 3000,
        });
      });
  }, []);

  function AboutHeader({ config }: { config: Config | null }) {
    return (
      <div className="flex ml-2 page-header">
        <h1 className="al">About {config ? config.application_name : ""}</h1>
      </div>
    );
  }

  function HelpfulLinks({ config }: { config: Config | null }) {
    if (!config) return <p>Loading configuration...</p>;
    return (
      <ul>
        <li>
          <Link to={`/swagger`}>Open API documentation</Link>-{" "}
          {config.application_name} uses OpenAPI Documentation for our ReST
          Interface.
        </li>
        {config.metrics_url && (
          <li>
            <a
              href={config.metrics_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Metrics
            </a>{" "}
            - Link to the configured metrics backend.
          </li>
        )}
        <li>
          <a
            href="https://grafana.com/dashboards/6621"
            target="_blank"
            rel="noopener noreferrer"
          >
            Grafana Dashboard ({config.application_name})
          </a>
          - A grafana dashboard for monitoring {config.application_name}
          performance.
        </li>
        <li>
          <a
            href="https://grafana.com/dashboards/6624"
            target="_blank"
            rel="noopener noreferrer"
          >
            Grafana Dashboard (Plugins)
          </a>
          - A grafana dashboard for monitoring {config.application_name}
          plugin performance.
        </li>
      </ul>
    );
  }

  function VersionInformation({
    config,
    version,
  }: {
    config: Config | null;
    version: Version | null;
  }) {
    if (!config || !version) return <p>Loading version information...</p>;
    return (
      <>
        <div>
          <span className="mr-1">
            {config.application_name} is currently on version
          </span>
          <span className="font-bold">{version.beer_garden_version}</span>
        </div>
        <div>
          <span className="mr-1">Python version</span>
          <span className="font-bold">{version.python_version}</span>
        </div>
      </>
    );
  }

  return (
    <div>
      <AboutHeader config={config} />
      <div className="flex">
        <Panel header="Helpful Links" className="m-2 flex-1">
          <>
            <HelpfulLinks config={config} />
          </>
        </Panel>
        <Panel header="Version Information" className="m-2 flex-1">
          <>
            <VersionInformation config={config} version={version} />
          </>
        </Panel>
      </div>
    </div>
  );
}

export default AboutIndex;
