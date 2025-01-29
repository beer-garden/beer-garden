import SystemView from "./SystemView";
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import CardGroup from 'react-bootstrap/CardGroup';
import Card from 'react-bootstrap/Card';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import InstanceView from './InstanceView';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import ButtonToolbar from 'react-bootstrap/ButtonToolbar';
import ListGroup from 'react-bootstrap/ListGroup';
import Dropdown from 'react-bootstrap/Dropdown';
import DropdownButton from 'react-bootstrap/DropdownButton';
import { Form } from 'react-bootstrap';
import React, { useState } from 'react';

import { System } from './brewtils-types';

import SampleSystems from './SampleSystems';
import SystemIndexGroups from "./SystemIndexGroups";

function SystemIndex() {

  const systems: Array<System> = SampleSystems();

  // const [filter, setFilter] = useState('');

  const filter = {name: '', group: '', status: ''};
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

  return (
    <Row>
      <Col>

        <Form>
          <Form.Group controlId="filterName">
            <Form.Label>Filter by Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter system name"
              value={filter.name}
              onChange={(e) => setFilter({ ...filter, name: e.target.value })}
            />
          </Form.Group>
          <Form.Group controlId="filterGroup">
            <Form.Label>Filter by Group</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter system group"
              value={filter.group}
              onChange={(e) => setFilter({ ...filter, group: e.target.value })}
            />
          </Form.Group>
          <Form.Group controlId="filterStatus">
            <Form.Label>Filter by Status</Form.Label>
            <Form.Control
              as="select"
              value={filter.status}
              onChange={(e) => setFilter({ ...filter, status: e.target.value })}
            >
              <option value="">Select status</option>
              <option value="INITIALIZING">INITIALIZING</option>
              <option value="RUNNING">RUNNING</option>
              <option value="PAUSED">PAUSED</option>
              <option value="STOPPED">STOPPED</option>
              <option value="DEAD">DEAD</option>
              <option value="UNRESPONSIVE">UNRESPONSIVE</option>
              <option value="STARTING">STARTING</option>
              <option value="STOPPING">STOPPING</option>
              <option value="UNKNOWN">UNKNOWN</option>
              <option value="AWAITING_SYSTEM">AWAITING_SYSTEM</option>
            </Form.Control>
          </Form.Group>
          <Button variant="primary" onClick={() => applyFilter()}>Apply Filter</Button>
        </Form>
      </Col>
      <Col xs={10}>
        <ButtonToolbar className="mb-3" aria-label="Toolbar with Button groups">
          <ButtonGroup aria-label="Basic example" style={{ marginLeft: "auto" }}>
            <Button variant="success" >Rescan Directory</Button>
            <Button variant="warning" >Clear All Queues</Button>
          </ButtonGroup>
        </ButtonToolbar>
        <Row xs={1} md={2} lg={4} className="g-4 mb-4">
          {filteredData &&
            filteredData.map((system) => {
              
              return (
                  <Card className="flex-fill" key={system.id} >
                    <Card.Body>
                      <Card.Header><FontAwesomeIcon icon="beer-mug-empty" /> {system.namespace} / {system.name} / {system.version}</Card.Header>
                      <Card.Text>{system.description}</Card.Text>
                      <Card.Text>
                        <ButtonToolbar className="mb-3" aria-label="Toolbar with Button groups">
                          <ButtonGroup aria-label="Basic example">
                            <Button variant="success"><FontAwesomeIcon icon="play" /></Button>
                            <Button variant="warning"><FontAwesomeIcon icon="stop" /></Button>
                            <Button variant="primary"><FontAwesomeIcon icon="arrows-rotate" /></Button>
                            <Button variant="danger"><FontAwesomeIcon icon="trash" /></Button>
                          </ButtonGroup>
                          <ButtonGroup aria-label="Basic example" style={{ marginLeft: "auto" }}>
                            <Button variant="primary" >Create Request</Button>
                          </ButtonGroup>
                        </ButtonToolbar>
                      </Card.Text>
                      <Card.Text>
                        <ListGroup>
                          {system.instances && system.instances.map((instance) => {
                            return (<InstanceView {...instance} />);
                          })}
                        </ ListGroup>
                      </Card.Text>
                    </Card.Body>
                  </Card>
              );
            })}
        </Row>
      </Col>
    </Row>
  )
}
export default SystemIndex;