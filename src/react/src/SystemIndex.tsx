import SystemView from "./SystemView";

import { Row, Col } from 'rsuite';
import InstanceView from './InstanceView';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

import { List } from 'rsuite';

import { Form, Checkbox, CheckboxGroup } from 'rsuite';
import React, { useState } from 'react';

import { System } from './brewtils-types';

import SampleSystems from './SampleSystems';
import SystemIndexGroups from "./SystemIndexGroups";

import { Card, CardGroup, Text } from 'rsuite';
import { Button, ButtonGroup, ButtonToolbar, IconButton, CheckPicker } from 'rsuite';
import StopOutlineIcon from '@rsuite/icons/StopOutline';
import PlayOutlineIcon from '@rsuite/icons/PlayOutline';
import ReloadIcon from '@rsuite/icons/Reload';
import TrashIcon from '@rsuite/icons/Trash';
import { Sidenav, Nav } from 'rsuite';
import DashboardIcon from '@rsuite/icons/legacy/Dashboard';

function SystemIndex() {

  const systems: Array<System> = SampleSystems();

  const filter = { name: '', group: '', status: '' };
  const filteredData = systems;

  const applyFilter = () => {
    console.log('apply filter');
  };
  const setFilter = (value: any) => {
    console.log('apply filter');
  };

  const [columns, setColumns] = React.useState(2);
  const [spacing, setSpacing] = React.useState(20);

  const instanceStatus = ["INITIALIZING", "RUNNING", "PAUSED", "STOPPED", "DEAD", "UNRESPONSIVE", "STARTING", "STOPPING", "UNKNOWN", "AWAITING_SYSTEM"].map(item => ({
    label: item,
    value: item
  }));

  return (
    <>
      {/* <ButtonToolbar className="mb-3" aria-label="Toolbar with Button groups">
        <ButtonGroup aria-label="Basic example" style={{ marginLeft: "auto" }}>
          <Button>Rescan Directory</Button>
          <Button>Clear All Queues</Button>
        </ButtonGroup>
      </ButtonToolbar> */}

      <Form layout="inline">
        <Form.Group controlId="filterName">
          <Form.ControlLabel>Filter by Name</Form.ControlLabel>
          <Form.Control
            type="text"
            name="filter.name"
          />
        </Form.Group>

        <Form.Group controlId="checkPicker">
          <Form.ControlLabel>Status:</Form.ControlLabel>
          <Form.Control name="checkPicker" accepter={CheckPicker} data={instanceStatus} />
        </Form.Group>

        <Form.Group>
          <ButtonToolbar>
            <Button appearance="primary">Apply Filter</Button>
            <Button appearance="default">Rescan Directory</Button>
            <Button appearance="default">Clear all Queues</Button>
          </ButtonToolbar>
        </Form.Group>
      </Form>


      <CardGroup spacing={spacing}>
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
    </>

  )
}
export default SystemIndex;