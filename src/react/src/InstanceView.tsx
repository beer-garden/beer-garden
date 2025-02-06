// import Button from 'react-bootstrap/Button';
// import ListGroup from 'react-bootstrap/ListGroup';
// import ButtonGroup from 'react-bootstrap/ButtonGroup';
// import Navbar from 'react-bootstrap/Navbar';
// import NavDropdown from 'react-bootstrap/NavDropdown';
// import Dropdown from 'react-bootstrap/Dropdown';
// import DropdownButton from 'react-bootstrap/DropdownButton';
// import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { Instance } from './brewtils-types';
// import Badge from 'react-bootstrap/Badge';
import MenuIcon from '@rsuite/icons/Menu';
import { Badge } from 'rsuite';
import { Button, ButtonGroup, ButtonToolbar, IconButton, CheckPicker } from 'rsuite';
import StopOutlineIcon from '@rsuite/icons/StopOutline';
import PlayOutlineIcon from '@rsuite/icons/PlayOutline';
import { Dropdown } from 'rsuite';
import { List } from 'rsuite';
import FolderIcon from '@rsuite/icons/Folder';
import TextImageIcon from '@rsuite/icons/TextImage';
import CloseOutlineIcon from '@rsuite/icons/CloseOutline';

import { Grid, Row, Col } from 'rsuite';
import { Navbar, Nav } from 'rsuite';

function InstanceView(instance: Instance) {
    return (<List.Item>

            <Row>
            <Col>
                <FolderIcon />         
            </Col >
            <Col>
                {instance.name}            
            </Col>
            <Col>
                <Badge color="green">
                    {instance.status}
                </Badge>
            </Col>
            

            </Row>
            <Row>
            
            <Col>
                <ButtonGroup>
                    <IconButton icon={<StopOutlineIcon />} appearance="default" >Stop</IconButton>
                    <IconButton icon={<PlayOutlineIcon />} appearance="default" >Start</IconButton>
                    <IconButton icon={<TextImageIcon />} appearance="default" >Logs</IconButton>
                    <IconButton icon={<CloseOutlineIcon />} appearance="default" >Cancel</IconButton>
                </ButtonGroup>
            </Col>
            </Row>

    </List.Item>)
}

export default InstanceView;