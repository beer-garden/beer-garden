import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Link,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";

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
      <Typography variant="h2" component="h1" sx={{ ml: 2 }}>
        About {config ? config.application_name : ""}
      </Typography>
    );
  }

  function HelpfulLinks({ config }: { config: Config | null }) {
    if (!config) return <p>Loading configuration...</p>;
    return (
      <ul>
        <li>
          <Link component={RouterLink} sx={{ mr: 0.5 }} to={`/swagger`}>
            Open API documentation
          </Link>
          - {config.application_name} uses OpenAPI Documentation for our ReST
          Interface.
        </li>
        {config.metrics_url && (
          <li>
            <Link
              sx={{ mr: 0.5 }}
              href={config.metrics_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Metrics
            </Link>
            - Link to the configured metrics backend.
          </li>
        )}
        <li>
          <Link
            sx={{ mr: 0.5 }}
            href="https://grafana.com/dashboards/6621"
            target="_blank"
            rel="noopener noreferrer"
          >
            Grafana Dashboard ({config.application_name})
          </Link>
          - A grafana dashboard for monitoring {config.application_name}{" "}
          performance.
        </li>
        <li>
          <Link
            sx={{ mr: 0.5 }}
            href="https://grafana.com/dashboards/6624"
            target="_blank"
            rel="noopener noreferrer"
          >
            Grafana Dashboard (Plugins)
          </Link>
          - A grafana dashboard for monitoring {config.application_name} plugin
          performance.
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
          <Box component="span" sx={{ mr: 1 }}>
            {config.application_name} is currently on version
          </Box>
          <Box component="span" sx={{ fontWeight: "bold" }}>
            {version.beer_garden_version}
          </Box>
        </div>
        <div>
          <Box component="span" sx={{ mr: 1 }}>
            Python version
          </Box>
          <Box component="span" sx={{ fontWeight: "bold" }}>
            {version.python_version}
          </Box>
        </div>
      </>
    );
  }

  return (
    <div>
      <AboutHeader config={config} />
      <Box
        sx={{
          display: "flex",
          alignItems: "flex-start",
          flexDirection: "row",
          ml: 2,
        }}
      >
        <Card variant="outlined" sx={{ mr: 2 }}>
          <CardHeader
            title={
              <Typography
                variant="h6"
                component="h2"
                sx={{ fontWeight: "bold" }}
              >
                Helpful Links
              </Typography>
            }
          />
          <Divider />
          <CardContent>
            <HelpfulLinks config={config} />
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ mr: 2, flexGrow: 1 }}>
          <CardHeader
            title={
              <Typography
                variant="h6"
                component="h2"
                sx={{ fontWeight: "bold" }}
              >
                Version Information
              </Typography>
            }
          />
          <Divider />
          <CardContent>
            <VersionInformation config={config} version={version} />
          </CardContent>
        </Card>
      </Box>
    </div>
  );
}

export default AboutIndex;
