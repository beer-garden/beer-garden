import React, { Component } from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { withStyles } from "@material-ui/core/styles";
import { Link } from "react-router-dom";
import Button from "@material-ui/core/Button";
import InputAdornment from "@material-ui/core/InputAdornment";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import AddIcon from "@material-ui/icons/Add";
import SearchIcon from "@material-ui/icons/Search";

const styles = theme => ({
  icon: { marginLeft: theme.spacing.unit },
  error: { color: theme.palette.error.dark },
  headerRow: {
    display: "flex",
    flexDirection: "row",
    marginBottom: theme.spacing.unit,
  },
  rightButton: { marginLeft: "auto" },
});

export class RoleListHeader extends Component {
  renderButton = () => {
    const { classes, canAdd, addRoute } = this.props;

    if (!canAdd) {
      return null;
    }

    return (
      <Button
        component={Link}
        to={addRoute}
        color="primary"
        className={classes.rightButton}
      >
        Add Role
        <AddIcon fontSize="small" className={classes.icon} />
      </Button>
    );
  };

  render() {
    const { classes, filterText, onFilterChange } = this.props;

    return (
      <>
        <div className={classes.headerRow}>
          <Typography variant="h4">Roles</Typography>
          {this.renderButton()}
        </div>
        <TextField
          label="Search roles..."
          value={filterText}
          onChange={onFilterChange}
          fullWidth
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </>
    );
  }
}

RoleListHeader.propTypes = {
  canAdd: PropTypes.bool.isRequired,
  addRoute: PropTypes.string.isRequired,
  filterText: PropTypes.string.isRequired,
  onFilterChange: PropTypes.func.isRequired,
};

const enhance = compose(withStyles(styles));

export default enhance(RoleListHeader);
