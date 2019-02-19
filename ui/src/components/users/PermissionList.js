import React from "react";
import PropTypes from "prop-types";
import { compose } from "recompose";
import { withStyles } from "@material-ui/core/styles";
import Checkbox from "@material-ui/core/Checkbox";
import Divider from "@material-ui/core/Divider";
import Typography from "@material-ui/core/Typography";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import TableCell from "@material-ui/core/TableCell";
import Clear from "@material-ui/icons/Clear";
import Check from "@material-ui/icons/Check";
import { CATEGORIES } from "../../constants/permissions";
import { hasPermissions } from "../../utils";

const styles = theme => ({
  root: {
    paddingTop: theme.spacing.unit * 2,
    paddingBottom: theme.spacing.unit * 2,
  },
  chip: {
    marginRight: theme.spacing.unit,
  },
  topPad: {
    paddingTop: theme.spacing.unit,
  },
  success: {
    color: theme.palette.success,
  },
});

export class PermissionList extends React.PureComponent {
  renderEditCell(permission) {
    const { permissions, togglePermission } = this.props;

    const hasPermission = hasPermissions(
      { permissions: permissions.map(p => p.value) },
      [permission],
    );
    const propPerm = permissions.find(perm => perm.value === permission);
    const disabled = propPerm ? propPerm.inherited : false;

    return (
      <Checkbox
        checked={hasPermission}
        onChange={togglePermission}
        value={permission}
        disabled={disabled}
      />
    );
  }

  renderPermissionCell(permission) {
    let el;
    const { edit, permissions } = this.props;

    if (edit) {
      el = this.renderEditCell(permission);
    } else {
      el = hasPermissions({ permissions }, [permission]) ? (
        <Check />
      ) : (
        <Clear />
      );
    }

    return <TableCell align="right">{el}</TableCell>;
  }

  renderBody() {
    const rows = [];
    for (let [key, value] of Object.entries(CATEGORIES)) {
      rows.push(
        <TableRow hover key={key}>
          <TableCell>
            <Typography variant="subtitle2">{key}</Typography>
          </TableCell>
          {this.renderPermissionCell(value["create"])}
          {this.renderPermissionCell(value["read"])}
          {this.renderPermissionCell(value["update"])}
          {this.renderPermissionCell(value["delete"])}
        </TableRow>,
      );
    }
    return <TableBody>{rows}</TableBody>;
  }

  render() {
    return (
      <>
        <Typography color="textSecondary">Permissions:</Typography>
        <Divider />
        <Table padding={"checkbox"}>
          <TableHead>
            <TableRow>
              <TableCell>Resource</TableCell>
              <TableCell align="right">Create</TableCell>
              <TableCell align="right">Read</TableCell>
              <TableCell align="right">Update</TableCell>
              <TableCell align="right">Delete</TableCell>
            </TableRow>
          </TableHead>
          {this.renderBody()}
        </Table>
      </>
    );
  }
}

PermissionList.propTypes = {
  classes: PropTypes.object.isRequired,
  edit: PropTypes.bool.isRequired,
  permissions: PropTypes.array.isRequired,
  togglePermission: PropTypes.func,
};

const enhance = compose(withStyles(styles));

export default enhance(PermissionList);
