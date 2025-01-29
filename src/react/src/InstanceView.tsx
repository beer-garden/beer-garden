import Button from 'react-bootstrap/Button';
import ListGroup from 'react-bootstrap/ListGroup';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import Dropdown from 'react-bootstrap/Dropdown';
import DropdownButton from 'react-bootstrap/DropdownButton';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { Instance } from './brewtils-types';
import Badge from 'react-bootstrap/Badge';
import { Row } from 'react-bootstrap';
import Col from 'react-bootstrap/Col';

function InstanceView(instance: Instance) {
    return (<ListGroup.Item>
        <Row>
            <Col>
                <FontAwesomeIcon icon="folder-open" /> {instance.name}            
            </Col>
            <Col>
                <Badge bg="success" pill>
                    {instance.status}
                </Badge>
            </Col>
            
            <Col>
                <ButtonGroup style={{ marginLeft: "auto" }}>
                    <Button variant="success"><FontAwesomeIcon icon="play" /></Button>
                    <Button variant="warning"><FontAwesomeIcon icon="stop" /></Button>

                    <DropdownButton as={ButtonGroup} title={<FontAwesomeIcon icon="bars" />} id="bg-nested-dropdown">
                        <Dropdown.Item eventKey="1">Logs</Dropdown.Item>
                        <Dropdown.Item eventKey="2">Clear Queue</Dropdown.Item>
                    </DropdownButton>
                </ButtonGroup>
            </Col>
        </Row>
    </ListGroup.Item>)
}

export default InstanceView;