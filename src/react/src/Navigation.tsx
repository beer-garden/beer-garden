import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';

function NavigationMenu() {
  return (
    <Navbar expand="lg" className="bg-body-tertiary">
      <Container>
        <Navbar.Brand href="#home" as="h1">Beer Garden</Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            <Nav.Link href="#system">Systems</Nav.Link>
            <Nav.Link href="#link">Requests</Nav.Link>
            <Nav.Link href="#link">Scheduler</Nav.Link>
            <Nav.Link href="#link">Create Request</Nav.Link>
            <NavDropdown title="Admin" id="basic-nav-dropdown">
              <NavDropdown.Item href="#action/3.1">About</NavDropdown.Item>
              <NavDropdown.Item href="#action/3.1">Garden</NavDropdown.Item>
              <NavDropdown.Item href="#action/3.1">Topics</NavDropdown.Item>
              <NavDropdown.Item href="#action/3.1">Users</NavDropdown.Item>
              <NavDropdown.Item href="#action/3.1">Roles</NavDropdown.Item>
            </NavDropdown>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default NavigationMenu;