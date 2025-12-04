import Container from 'react-bootstrap/Container';
// import Nav from 'react-bootstrap/Nav';
// import Navbar from 'react-bootstrap/Navbar';
// import NavDropdown from 'react-bootstrap/NavDropdown';
// import { Navbar, Nav } from 'rsuite';

// function NavigationMenu() {
//   return (
//     <Navbar>
//     <Navbar.Brand href="#home">Beer Garden</Navbar.Brand>
//     <Nav pullRight>
//       <Nav.Item>Systems</Nav.Item>
//       <Nav.Item>Requests</Nav.Item>
//       <Nav.Item>Scheduler</Nav.Item>
//       <Nav.Item>Create Request</Nav.Item>
//       <Nav.Menu title="Admin">
//         <Nav.Item>About</Nav.Item>
//         <Nav.Item>Garden</Nav.Item>
//         <Nav.Item>Topics</Nav.Item>
//         <Nav.Item>Users</Nav.Item>
//         <Nav.Item>Roles</Nav.Item>
//       </Nav.Menu>
//     </Nav>
//   </Navbar>
//   );
// }
import { MegaMenu } from 'primereact/megamenu';
import { MenuItem } from 'primereact/menuitem';

function NavigationMenu() {

  const items: MenuItem[] = [
    {
      label: 'Systems',
    },
    {
      label: 'Requests',
    },
    {
      label: 'Scheduler',
    },
    {
      label: 'Create Request',
    },
    {
      label: 'Admin',
      items: [
        { label: 'About', icon: 'pi pi-list' },
        { label: 'Garden', icon: 'pi pi-users' },
        { label: 'Topics', icon: 'pi pi-file' },
        { label: 'Users', icon: 'pi pi-file' },
        { label: 'Roles', icon: 'pi pi-file' }
      ]
    },
  ];

  return (
    <div className="card">
      <MegaMenu model={items} breakpoint="960px" />
    </div>
  )

}

export default NavigationMenu;