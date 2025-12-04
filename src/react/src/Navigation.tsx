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

import { MenuItem } from 'primereact/menuitem';
import React from 'react';
import { MegaMenu } from 'primereact/megamenu';
import { InputText } from 'primereact/inputtext';
import { Ripple } from 'primereact/ripple';
import { Button } from 'primereact/button';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

function NavigationMenu() {

  // const items: MenuItem[] = [
  //   {
  //     label: 'Systems',
  //   },
  //   {
  //     label: 'Requests',
  //   },
  //   {
  //     label: 'Scheduler',
  //   },
  //   {
  //     label: 'Create Request',
  //   },
  //   {
  //     label: 'Admin',
  //     items: [
  //       { label: 'About', icon: 'pi pi-list' },
  //       { label: 'Garden', icon: 'pi pi-users' },
  //       { label: 'Topics', icon: 'pi pi-file' },
  //       { label: 'Users', icon: 'pi pi-file' },
  //       { label: 'Roles', icon: 'pi pi-file' }
  //     ]
  //   },
  // ];

  // return (
  //   <div className="card">
  //     <MegaMenu model={items} breakpoint="960px" />
  //   </div>
  // )

  const itemRenderer = (item: any, options: any) => {
    if (item.root) {
        return (
            <a className="flex align-items-center cursor-pointer px-3 py-2 overflow-hidden relative font-semibold text-lg uppercase p-ripple hover:surface-ground" style={{ borderRadius: '2rem' }} onClick={(e) => options.onClick(e)}>
                <FontAwesomeIcon icon={item.icon} />
                <span className="ml-2">{item.label}</span>
                <Ripple />
            </a>
        );
    } else if (!item.image) {
        return (
            <a className="flex align-items-center p-3 cursor-pointer mb-2 gap-2 " onClick={options.onClick}>
                <span className="inline-flex align-items-center justify-content-center border-circle bg-primary w-3rem h-3rem">
                  <FontAwesomeIcon icon={item.icon} />
                </span>
                <span className="inline-flex flex-column gap-1">
                    <span className="font-medium text-lg text-900">{item.label}</span>
                    <span className="white-space-nowrap">{item.subtext}</span>
                </span>
            </a>
        );
    } else {
        return (
            <div className="flex flex-column align-items-start gap-3" onClick={options.onClick}>
                <img alt="megamenu-demo" src={item.image} className="w-full" />
                <span>{item.subtext}</span>
                <Button className="p-button p-component p-button-outlined" label={item.label} />
            </div>
        );
    }
};

const items = [
    {
        label: 'Systems',
        root: true,
        template: itemRenderer
    },
    {
        label: 'Requests',
        root: true,
        template: itemRenderer
    },
    {
      label: 'Scheduler',
      root: true,
      template: itemRenderer
  },
  {
    label: 'Create Request',
    root: true,
    template: itemRenderer
},
    {
        label: 'Admin',
        root: true,
        template: itemRenderer,
        items: [
            [
                {
                    items: [
                        { label: 'About', icon: 'info', subtext: 'Subtext of item', template: itemRenderer },
                        { label: 'Garden', icon: 'globe', subtext: 'Subtext of item', template: itemRenderer },
                        { label: 'Topics', icon: 'envelope', subtext: 'Subtext of item', template: itemRenderer },
                        { label: 'Users', icon: 'user', subtext: 'Subtext of item', template: itemRenderer },
                        { label: 'Roles', icon: 'users', subtext: 'Subtext of item', template: itemRenderer }
                    ]
                }
            ]
        ]
    }
    
];

const start = (
  <FontAwesomeIcon icon="beer-mug-empty"/>
);


return (
    <div className="card">
        <MegaMenu model={items} orientation="horizontal" start={start} breakpoint="960px" className="p-3 surface-0 shadow-2" style={{ borderRadius: '3rem' }} />
    </div>
)

}

export default NavigationMenu;