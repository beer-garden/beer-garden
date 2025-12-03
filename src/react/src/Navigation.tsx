import Container from 'react-bootstrap/Container';
// import Nav from 'react-bootstrap/Nav';
// import Navbar from 'react-bootstrap/Navbar';
// import NavDropdown from 'react-bootstrap/NavDropdown';
import { Navbar, Nav } from 'rsuite';

function NavigationMenu() {
  return (
    <Navbar>
    <Navbar.Brand href="#home">Beer Garden</Navbar.Brand>
    <Nav pullRight>
      <Nav.Item>Systems</Nav.Item>
      <Nav.Item>Requests</Nav.Item>
      <Nav.Item>Scheduler</Nav.Item>
      <Nav.Item>Create Request</Nav.Item>
      <Nav.Menu title="Admin">
        <Nav.Item>About</Nav.Item>
        <Nav.Item>Garden</Nav.Item>
        <Nav.Item>Topics</Nav.Item>
        <Nav.Item>Users</Nav.Item>
        <Nav.Item>Roles</Nav.Item>
      </Nav.Menu>
    </Nav>
  </Navbar>
  );
}

export default NavigationMenu;