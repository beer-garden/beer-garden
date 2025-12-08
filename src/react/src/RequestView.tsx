import { Accordion, Card, Button, ButtonGroup, ButtonToolbar } from "react-bootstrap";
import { Request } from './brewtils-types';
import { Form } from 'react-bootstrap';
import Breadcrumb from 'react-bootstrap/Breadcrumb';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

// import RequestGantt from "./RequestGantt";

// import { Gantt } from "wx-react-gantt";

// import * as MyPackage from 'wx-react-gantt';
// console.log(Object.keys(MyPackage)); 
// import "wx-react-gantt/dist/gantt.css";
// import { Gantt, WillowDark, task, link } from "wx-react-gantt";

// import { RequestGantt } from './RequestGantt';
import RequestTimeline from "./RequestTimeline"
// import ApexTimeline from "./ApexTimeline";
// import RequestHistory from "./RequestHistory";
// import RequestGanttHistory from "./RequestGanttHistory";
import RequestTreeChart from "./RequestTreeChart";


function ExampleRequest() {
    const request: Request = {
        "system_version": "3.0.0.dev0",
        "id": "6772ed28aa78c5898091e9e7",
        "output": "Happy World!",
        "parent": null,
        "command_type": "ACTION",
        "updated_at": 1735585075473,
        "namespace": "default",
        "output_type": "STRING",
        "is_event": false,
        "command": "sleep_say",
        "status": "SUCCESS",

        "created_at": 1735585064780,
        "system": "echo-sleeper",
        "instance_name": "default",
        "metadata": {
            "CREATED_default": 1735603064781,
            "IN_PROGRESS_default": 1735603064915,
            "SUCCESS_default": 1735603075474
        },
        "target_garden": "default",
        "status_updated_at": 1735585075474,
        "source_garden": "default",
        "parameters": {
            "message": "Happy World!",
            "loud": false,
            "amount": 10
        },
        "hidden": false,
        "has_parent": false,
        "children": [
            {
                "system_version": "3.0.0.dev0",
                "id": "6772ed29aa78c5898091e9ee",
                "output": "null",
                "command_type": "ACTION",
                "updated_at": 1735585075214,
                "namespace": "default",
                "output_type": "STRING",
                "is_event": false,
                "command": "sleep",
                "status": "SUCCESS",

                "created_at": 1735585065046,
                "system": "sleeper",
                "instance_name": "default",
                "metadata": {
                    "CREATED_default": 1735603065046,
                    "IN_PROGRESS_default": 1735603065131,
                    "SUCCESS_default": 1735603075216
                },
                "target_garden": "default",
                "status_updated_at": 1735585075216,
                "source_garden": "default",
                "parameters": {
                    "amount": 10
                },
                "hidden": false,
                "has_parent": true,

                "command_display_name": "sleep",
                "comment": null
            },
            {
                "system_version": "3.0.0.dev0",
                "id": "6772ed33aa78c5898091ea5d",
                "output": "Happy World!",
                "command_type": "ACTION",
                "updated_at": 1735585075434,
                "namespace": "default",
                "output_type": "STRING",
                "is_event": false,
                "command": "say",
                "status": "SUCCESS",

                "created_at": 1735585075334,
                "system": "echo",
                "instance_name": "default",
                "metadata": {
                    "CREATED_default": 1735603075334,
                    "IN_PROGRESS_default": 1735603075400,
                    "SUCCESS_default": 1735603075436
                },
                "target_garden": "default",
                "status_updated_at": 1735585075436,
                "source_garden": "default",
                "parameters": {
                    "message": "Happy World!",
                    "loud": false
                },
                "hidden": false,
                "has_parent": true,

                "command_display_name": "say",
                "comment": null
            }
        ],

        "command_display_name": "sleep_say",
        "comment": ""
    }

    return request;
}

function RequestHeader(request: Request) {
    return (<div>
        <h3>Request View {request.id}</h3>
        <ButtonToolbar className="mb-3" aria-label="Toolbar with Button groups">
            <ButtonGroup aria-label="Basic example" style={{ marginLeft: "auto" }}>
                <Button variant="danger" >Delete</Button>
            </ButtonGroup>
        </ButtonToolbar>
    </div>)
}


function RequestOutput(request: Request) {
    return (
        <div>
            <ButtonToolbar className="mb-3" aria-label="Toolbar with Button groups">
                <ButtonGroup aria-label="Basic example" style={{ marginLeft: "auto" }}>
                    <Button variant="success" ><FontAwesomeIcon icon="download" /></Button>
                </ButtonGroup>
            </ButtonToolbar>
            <Form>
                <Form.Group className="mb-3" controlId="system.group">

                    <Form.Control as="textarea" defaultValue={request.output} rows={3} readOnly />
                </Form.Group>
            </Form>
        </div>
    )
}

function RequestInput(request: Request) {
    return (
        <div>
            
            <Breadcrumb>
                <Breadcrumb.Item active>{request.namespace}</Breadcrumb.Item>
                <Breadcrumb.Item active>{request.system}</Breadcrumb.Item>
                <Breadcrumb.Item active>{request.system_version}</Breadcrumb.Item>
                <Breadcrumb.Item active>{request.instance_name}</Breadcrumb.Item>
                <Breadcrumb.Item active>{request.command}</Breadcrumb.Item>
            </Breadcrumb>
            <div>Command Description</div>
            <Form>
                <Form.Group className="mb-3">
                    <Form.Label>message</Form.Label>
                    <Form.Control type="text" defaultValue="Happy World!" readOnly disabled />
                    <Form.Text muted>The message</Form.Text>
                </Form.Group>
                <Form.Group className="mb-3">
                    <Form.Label>loud</Form.Label>
                    <Form.Check
                        type='checkbox'
                        readOnly disabled
                    />
                    <Form.Text muted>Add exclamation marks</Form.Text>
                </Form.Group>
                <Form.Group className="mb-3">
                    <Form.Label>amount</Form.Label>
                    <Form.Control type="text" defaultValue="10" readOnly disabled />
                    <Form.Text muted>How long to sleep</Form.Text>
                </Form.Group>
            </Form>
            <ButtonToolbar className="mb-3" aria-label="Toolbar with Button groups">
                <ButtonGroup aria-label="Basic example" style={{ marginLeft: "auto" }}>
                    <Button variant="warning" >Pour It Again</Button>
                </ButtonGroup>
            </ButtonToolbar>
        </div>
    )
}

function RequestView() {

    const request: Request = ExampleRequest();

    return (
        <div>
            <RequestHeader {...request} />
            <Accordion defaultActiveKey={['1']} alwaysOpen>
                <Accordion.Item eventKey="1">
                    <Accordion.Header>Scheduler</Accordion.Header>
                    <Accordion.Body>
                        
                    </Accordion.Body>
                </Accordion.Item>
            </Accordion>
            <Accordion defaultActiveKey={['1']} alwaysOpen>
                <Accordion.Item eventKey="1">
                    <Accordion.Header>Select Commmand</Accordion.Header>
                    <Accordion.Body>
                        
                    </Accordion.Body>
                </Accordion.Item>
            </Accordion>
            <Accordion defaultActiveKey={['1']} alwaysOpen>
                <Accordion.Item eventKey="1">
                    <Accordion.Header>Input</Accordion.Header>
                    <Accordion.Body>
                        <RequestInput {...request} />
                    </Accordion.Body>
                </Accordion.Item>
            </Accordion>
            <Accordion defaultActiveKey={['1']} alwaysOpen>
                <Accordion.Item eventKey="1">
                    <Accordion.Header>Request History</Accordion.Header>
                    <Accordion.Body>
                        {/* <RequestTreeChart {...request} /> */}
                         {/* <RequestHistory {...request} />  */}
                        {/* <ApexTimeline {...request} />*/}
                        {/* <RequestGanttHistory {...request} /> */}
                    </Accordion.Body>
                </Accordion.Item>
            </Accordion>
            <Accordion defaultActiveKey={['1']} alwaysOpen>
                <Accordion.Item eventKey="1">
                    <Accordion.Header>Output</Accordion.Header>
                    <Accordion.Body>
                        <RequestOutput {...request} />
                    </Accordion.Body>
                </Accordion.Item>
            </Accordion>
        </div>
    )
}

export default RequestView;