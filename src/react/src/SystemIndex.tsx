import SystemView from "./SystemView";
// import Row from 'react-bootstrap/Row';
// import Col from 'react-bootstrap/Col';
import { Row, Col } from 'rsuite';
// import Button from 'react-bootstrap/Button';
// import CardGroup from 'react-bootstrap/CardGroup';
// import Card from 'react-bootstrap/Card';
// import ButtonGroup from 'react-bootstrap/ButtonGroup';
import InstanceView from './InstanceView';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
// import ButtonToolbar from 'react-bootstrap/ButtonToolbar';
// import ListGroup from 'react-bootstrap/ListGroup';
import { List } from 'rsuite';
// import Dropdown from 'react-bootstrap/Dropdown';
// import DropdownButton from 'react-bootstrap/DropdownButton';
// import { Form } from 'react-bootstrap';
import { Form, Checkbox, CheckboxGroup } from 'rsuite';
import React, { useState } from 'react';

import { System } from './brewtils-types';

import SampleSystems from './SampleSystems';
import SystemIndexGroups from "./SystemIndexGroups";

import { Card, CardGroup, Text } from 'rsuite';
import { Button, ButtonGroup, ButtonToolbar, IconButton } from 'rsuite';
import StopOutlineIcon from '@rsuite/icons/StopOutline';
import PlayOutlineIcon from '@rsuite/icons/PlayOutline';
import ReloadIcon from '@rsuite/icons/Reload';
import TrashIcon from '@rsuite/icons/Trash';


function SystemIndex() {

  const systems: Array<System> = SampleSystems();

  // const [filter, setFilter] = useState('');

  const filter = { name: '', group: '', status: '' };
  const filteredData = systems;
  // const filteredData = filter === ''
  //   ? systems
  //   : systems.filter(system => system.name === filter);

  const applyFilter = () => {
    console.log('apply filter');
  };
  const setFilter = (value: any) => {
    console.log('apply filter');
  };

  const [columns, setColumns] = React.useState(2);
  const [spacing, setSpacing] = React.useState(20);

  return (
    <Row>
      <Col>

        <Form>
          <Form.Group controlId="filterName">
            <Form.ControlLabel>Filter by Name</Form.ControlLabel>
            <Form.Control
              type="text"
              name="filter.name"
            />
          </Form.Group>
          <Form.Group controlId="filterGroup">
            <Form.ControlLabel>Filter by Group</Form.ControlLabel>
            <Form.Control
              type="text"
              name="filter.group"
            />
          </Form.Group>
          <Form.Group controlId="filterStatus">
            <Form.ControlLabel>Filter by Status</Form.ControlLabel>
            <Form.Control name="checkbox" accepter={CheckboxGroup} inline>
              <Checkbox value="INITIALIZING">INITIALIZING</Checkbox>
              <Checkbox value="RUNNING">RUNNING</Checkbox>
              <Checkbox value="PAUSED">PAUSED</Checkbox>
              <Checkbox value="STOPPED">STOPPED</Checkbox>
              <Checkbox value="DEAD">DEAD</Checkbox>
              <Checkbox value="UNRESPONSIVE">UNRESPONSIVE</Checkbox>
              <Checkbox value="STARTING">STARTING</Checkbox>
              <Checkbox value="STOPPING">STOPPING</Checkbox>
              <Checkbox value="UNKNOWN">UNKNOWN</Checkbox>
              <Checkbox value="AWAITING_SYSTEM">AWAITING_SYSTEM</Checkbox>
            </Form.Control>
          </Form.Group>
          <Form.Group>
            <ButtonToolbar>
              <Button appearance="primary">Apply Filter</Button>
              <Button appearance="default">Clear filter</Button>
            </ButtonToolbar>
          </Form.Group>
        </Form>
      </Col>
      <Col xs={10}>
        <ButtonToolbar className="mb-3" aria-label="Toolbar with Button groups">
          <ButtonGroup aria-label="Basic example" style={{ marginLeft: "auto" }}>
            <Button  >Rescan Directory</Button>
            <Button  >Clear All Queues</Button>
          </ButtonGroup>
        </ButtonToolbar>
        <CardGroup spacing={spacing}>
          {/* <Row xs={1} md={2} lg={4} className="g-4 mb-4"> */}
          {filteredData &&
            filteredData.map((system) => {

              return (
                <Card className="flex-fill" key={system.id} >
                  <Card.Header><FontAwesomeIcon icon="beer-mug-empty" /> {system.namespace} / {system.name} / {system.version}</Card.Header>
                  <Card.Body>

                    <Text>{system.description}</Text>
                    <Text>
                      <ButtonToolbar className="mb-3" aria-label="Toolbar with Button groups">
                        <ButtonGroup aria-label="Basic example">
                          {/* <Button ><FontAwesomeIcon icon="play" /></Button>
                            <Button ><FontAwesomeIcon icon="stop" /></Button>
                            <Button ><FontAwesomeIcon icon="arrows-rotate" /></Button>
                            <Button ><FontAwesomeIcon icon="trash" /></Button> */}
                          <IconButton circle icon={<StopOutlineIcon />} appearance="default" />
                          <IconButton circle icon={<PlayOutlineIcon />} appearance="default" />
                          <IconButton circle icon={<ReloadIcon />} appearance="default" />
                          <IconButton circle icon={<TrashIcon />} appearance="default" />
                        </ButtonGroup>
                        <ButtonGroup aria-label="Basic example" style={{ marginLeft: "auto" }}>
                          <Button >Create Request</Button>
                        </ButtonGroup>
                      </ButtonToolbar>
                    </Text>
                    <Text>
                      <List>
                        {system.instances && system.instances.map((instance) => {
                          return (<InstanceView {...instance} />);
                        })}
                      </ List>
                    </Text>
                  </Card.Body>
                </Card>
              );
            })}
        </CardGroup>
      </Col>
    </Row>
  )
}
export default SystemIndex;