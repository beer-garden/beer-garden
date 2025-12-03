import SystemView from "./SystemView";
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import InstanceView from './InstanceView';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import ButtonToolbar from 'react-bootstrap/ButtonToolbar';
import ListGroup from 'react-bootstrap/ListGroup';
import Dropdown from 'react-bootstrap/Dropdown';
import DropdownButton from 'react-bootstrap/DropdownButton';
import { Form } from 'react-bootstrap';
import React, { useState } from 'react';
import { Accordion, Card, Button } from "react-bootstrap";

import { System } from './brewtils-types';

import SampleSystems from './SampleSystems';

// function groupByKey(array: Array<System>, key: String) {
//   return array.reduce((objectsByKeyValue, obj: System) => {
//     const value = obj[key];
//     objectsByKeyValue[value] = (objectsByKeyValue[value] || []).concat(obj);
//     return objectsByKeyValue;
//   }, {});
// }

function groupBy<T, K extends keyof T>(array: T[], key: K): Record<string, T[]> {
  return array.reduce((result, item) => {
    const groupKey = item[key] as unknown as string; // Convert to string for object keys
    (result[groupKey] ||= []).push(item);
    return result;
  }, {} as Record<string, T[]>);
}

function SystemIndexGroups() {

  const groupedData = groupBy(SampleSystems(), "name");

  // const [activeIndex, setActiveIndex] = useState(null);

  // const handleClick = (index) => {
  //   setActiveIndex(index === activeIndex ? null : index);
  // };

  return (
    <Row>
      <Col>
        <Form>
          <Form.Label>
            <h2>Filter Systems</h2>
          </Form.Label>
          <Form.Group className="mb-3" controlId="system.name">
            <Form.Label>System Name</Form.Label>
            <Form.Control type="text" placeholder="System Name" />
          </Form.Group>
          <Form.Group className="mb-3" controlId="system.group">
            <Form.Label>Group</Form.Label>
            <Form.Control type="text" placeholder="Group" />
          </Form.Group>
          <Form.Group className="mb-3" controlId="system.status">
            <Form.Label>System Status</Form.Label>
            {["INITIALIZING",
              "RUNNING",
              "PAUSED",
              "STOPPED",
              "DEAD",
              "UNRESPONSIVE",
              "STARTING",
              "STOPPING",
              "UNKNOWN",
              "AWAITING_SYSTEM",].map((status) => (
                <Form.Check // prettier-ignore
                  type='checkbox'
                  id={`${status}-checkbox`}
                  label={status}
                />
              ))}

          </Form.Group>
          <Form.Group className="mb-3" controlId="system.groupBy">
            <Form.Label>Group By</Form.Label>
            {["System",
              "Namespace",
              "Status",
              "Version",
              "Group",].map((groupBy) => (
                <Form.Check // prettier-ignore
                  type='radio'
                  id={`${groupBy}-radio`}
                  label={groupBy}
                />
              ))}

          </Form.Group>
        </Form>
      </Col>
      <Col xs={10}>
        <ButtonToolbar className="mb-3" aria-label="Toolbar with Button groups">
          <ButtonGroup aria-label="Basic example" style={{ marginLeft: "auto" }}>
            <Button variant="success" >Rescan Directory</Button>
            <Button variant="warning" >Clear All Queues</Button>
          </ButtonGroup>
        </ButtonToolbar>
        <Row>
          <Accordion alwaysOpen>
            {Object.keys(groupedData).map((category) => (
              <Accordion.Item eventKey="${category}">
                <Accordion.Header>
                  {category}
                </Accordion.Header>
                <Accordion.Body>
                  <Row lg={3} sm={1}>
                    {groupedData[category] &&
                      groupedData[category].map((system) => {

                        return (
                          <Col className="d-flex">
                            <Card className="flex-fill" key={system.id}>
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
                          </Col>
                        );
                      })}
                  </Row>

                </Accordion.Body>
              </Accordion.Item>
            ))}
          </Accordion>

        </Row>
      </Col>
    </Row>
  )
}
export default SystemIndexGroups;