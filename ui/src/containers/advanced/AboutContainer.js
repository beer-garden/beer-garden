import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { connect } from "react-redux";
import { Grid } from "@material-ui/core";
import { loadVersion } from "../../actions/version";
import VersionInfo from "../../components/advanced/VersionInfo";
import HelpfulLinks from "../../components/advanced/HelpfulLinks";

export class AboutContainer extends Component {
  componentDidMount() {
    this.props.loadVersion();
  }

  render() {
    const { versionLoading, version, versionError, config } = this.props;

    return (
      <Grid container spacing={24}>
        <Grid item xs={12}>
          <HelpfulLinks config={config} />
        </Grid>
        <Grid item xs={12}>
          <VersionInfo
            loading={versionLoading}
            version={version}
            error={versionError}
          />
        </Grid>
      </Grid>
    );
  }
}

AboutContainer.propTypes = {
  version: PropTypes.object.isRequired,
  versionLoading: PropTypes.bool.isRequired,
  versionError: PropTypes.object,
  config: PropTypes.object.isRequired,
};

const mapStateToProps = state => {
  return {
    version: state.versionReducer.version,
    versionLoading: state.versionReducer.versionLoading,
    versionError: state.versionReducer.versionError,
    config: state.configReducer.config,
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadVersion: () => dispatch(loadVersion()),
  };
};

const enhance = compose(
  connect(
    mapStateToProps,
    mapDispatchToProps,
  ),
);

export default enhance(AboutContainer);
