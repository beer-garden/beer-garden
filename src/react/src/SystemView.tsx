import Button from 'react-bootstrap/Button';
import Card from 'react-bootstrap/Card';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import InstanceView from './InstanceView';

function SystemView() {
  return (
    <Card style={{ width: '25rem' }} border='danger'  >
      <Card.Body>
        <Card.Title>Namespace / System / Version</Card.Title>
        <Card.Text>
          The description of the system.
        </Card.Text>
        <ButtonGroup aria-label="Basic example">
            <Button variant="primary">Start</Button>
            <Button variant="primary">Stop</Button>
            <Button variant="primary">Restart</Button>
            <Button variant="primary">Delete</Button>
            <Button variant="primary">Create Request</Button>
        </ButtonGroup>
        <InstanceView />
      </Card.Body>
    </Card>
  );
}

export default SystemView;