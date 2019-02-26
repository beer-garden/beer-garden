import React, { Component } from "react";
import PropTypes from "prop-types";
import { withRouter, Link } from "react-router-dom";
import Divider from "@material-ui/core/Divider";
import Hidden from "@material-ui/core/Hidden";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import Extension from "@material-ui/icons/Extension";
import Help from "@material-ui/icons/Help";
import ViewHeadline from "@material-ui/icons/ViewHeadline";
import People from "@material-ui/icons/People";
import HowToReg from "@material-ui/icons/HowToReg";
import { hasPermissions } from "../../utils";
import { ROLE_READ, USER_READ } from "../../constants/permissions";

export class AdvancedIndex extends Component {
  allElements = [
    {
      id: "aboutLink",
      authRequired: false,
      primary: "About",
      to: "/about",
      icon: <Help fontSize="large" />,
      secondary:
        "Basic Information about this installation including version numbers and where to find API documentation",
    },
    {
      id: "sysMgmtLink",
      authRequired: false,
      primary: "Systems Management",
      to: "/systems",
      icon: <Extension fontSize="large" />,
      secondary: "Start, stop, reload, and delete registered systems.",
    },
    {
      id: "qMgmtLink",
      authRequired: false,
      primary: "Queue Management",
      to: "/queues",
      icon: <ViewHeadline fontSize="large" />,
      secondary: "Check plugin queue sizes, and clear out queues.",
    },
    {
      id: "usrMgmtLink",
      authRequired: true,
      permissions: [USER_READ],
      primary: "User Management",
      to: "/users",
      icon: <People fontSize="large" />,
      secondary: "Create, update, and delete users and their roles.",
    },
    {
      id: "roleMgmtLink",
      authRequired: true,
      permissions: [ROLE_READ],
      primary: "Role Management",
      to: "/roles",
      icon: <HowToReg fontSize="large" />,
      secondary: "Create, update, and delete roles.",
    },
  ];

  getVisibleElements = () => {
    const { authEnabled, userData } = this.props;

    return this.allElements.filter(element => {
      if (!element.authRequired) {
        return true;
      } else if (authEnabled && hasPermissions(userData, element.permissions)) {
        return true;
      } else {
        return false;
      }
    });
  };

  render() {
    const { match } = this.props;
    const visibleElements = this.getVisibleElements(this.allElements);
    const items = visibleElements.map((item, index) => (
      <React.Fragment key={item.id}>
        <ListItem
          id={item.id}
          key={item.id}
          button
          component={Link}
          to={`${match.url}${item.to}`}
        >
          <ListItemIcon>{item.icon}</ListItemIcon>
          <Hidden xsDown>
            <ListItemText
              primary={item.primary}
              primaryTypographyProps={{ gutterBottom: true, variant: "h4" }}
              secondary={item.secondary}
            />
          </Hidden>
          <Hidden smUp>
            <ListItemText
              primary={item.primary}
              primaryTypographyProps={{ gutterBottom: true, variant: "h4" }}
            />
          </Hidden>
        </ListItem>
        {index !== visibleElements.length - 1 && <Divider />}
      </React.Fragment>
    ));
    return <List>{items}</List>;
  }
}

AdvancedIndex.propTypes = {
  authEnabled: PropTypes.bool.isRequired,
  userData: PropTypes.object.isRequired,
};

export default withRouter(AdvancedIndex);
