import { Request, System } from '../models/brewtils-types';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { BreadCrumb } from 'primereact/breadcrumb';
import RequestTreeChart from "../components/RequestTreeChart";
import { Steps } from 'primereact/steps';
import { Toast } from 'primereact/toast';
import { useState, useRef, use, useEffect } from 'react';
import { MenuItem } from 'primereact/menuitem';
import { Button } from 'primereact/button';
import { Menubar } from 'primereact/menubar';
import CommandForm  from '../components/CommandForm';
import RequestOutput from '../components/RequestOutput';
import { Splitter, SplitterPanel } from 'primereact/splitter';
import { Stepper } from 'primereact/stepper';
import { StepperPanel } from 'primereact/stepperpanel';
import { Message } from 'primereact/message';
import { SplitButton } from 'primereact/splitbutton';
import {useParams} from 'react-router-dom'; 

import {GetRequest} from '../services/request_service';
import {GetSystemList} from '../services/system_service';

function ExampleSystem() {
    const system : System = {
        id: '6932016e45c60d9fef2ed235',
        name: 'echo',
        description: 'Annoying plugin that just repeats stuff',
        version: '3.0.0.dev0',
        namespace: 'default',
        max_instances: -1,
        instances: [
          {
            id: '6932016d45c60d9fef2ed231',
            name: '1',
            status: 'RUNNING',
            status_info: {},
            metadata: {},
          }
        ],
        commands: [
          {
            name: 'say',
            display_name: 'say',
            description: 'Echos!',
            parameters: [
              {
                key: 'message',
                type: 'String',
                multi: false,
                display_name: 'message',
                optional: true,
                default: 'Hello, World!',
                description: 'The Message to be Echoed',
                nullable: false,
                type_info: {},
                parameters: []
              },
              {
                key: 'message_choices',
                type: 'String',
                multi: true,
                display_name: 'message',
                optional: true,
                default: 'Hello, World!',
                choices: {
                    type: 'static',
                    strict: true,
                    value: ['Hello, World!', "test","1"]
                },
                description: 'The Message to be Echoed',
                nullable: false,
                type_info: {},
                parameters: []
              },
              {
                key: 'loud',
                type: 'Boolean',
                multi: false,
                display_name: 'loud',
                optional: true,
                default: true,
                description: 'Determines if Exclamation marks are added',
                nullable: true,
                type_info: {},
                parameters: []
              },
              {
                key: 'Integer',
                type: 'Integer',
                multi: true,
                display_name: 'Integer',
                optional: true,
                default: null,
                description: 'Determines if Exclamation marks are added',
                nullable: false,
                type_info: {},
                parameters: []
              },
              {
                key: 'Float',
                type: 'Float',
                multi: false,
                display_name: 'Float',
                optional: true,
                default: null,
                description: 'Determines if Exclamation marks are added',
                nullable: false,
                type_info: {},
                parameters: []
              },
              {
                key: 'Date',
                type: 'Date',
                multi: true,
                display_name: 'Date',
                optional: true,
                default: null,
                description: 'Determines if Exclamation marks are added',
                nullable: false,
                type_info: {},
                parameters: []
              },
              {
                key: 'DateTime',
                type: 'DateTime',
                multi: true,
                display_name: 'DateTime',
                optional: true,
                default: null,
                description: 'Determines if Exclamation marks are added',
                nullable: false,
                type_info: {},
                parameters: []
              },
              {
                key: 'Bytes',
                type: 'Bytes',
                multi: false,
                display_name: 'Bytes',
                optional: true,
                default: null,
                description: 'Determines if Exclamation marks are added',
                nullable: false,
                type_info: {},
                parameters: []
              },
              {
                key: 'Base64',
                type: 'Base64',
                multi: false,
                display_name: 'Base64',
                optional: true,
                default: null,
                description: 'Determines if Exclamation marks are added',
                nullable: false,
                type_info: {},
                parameters: []
              }
            ],
            command_type: 'ACTION',
            output_type: 'STRING',
            schema: {},
            form: {},
            hidden: false,
            metadata: {},
            tags: [],
            topics: [],
            allow_any_kwargs: false
          },
          {
            name: 'say_html',
            display_name: 'say_html',
            description: 'Echos with HTML output_type',
            parameters: [
              {
                key: 'message',
                type: 'String',
                multi: false,
                display_name: 'message',
                optional: true,
                default: '<h1>Hello, World</h1>',
                description: 'The Message to be Echoed',
                nullable: false,
                type_info: {},
                parameters: []
              }
            ],
            command_type: 'ACTION',
            output_type: 'HTML',
            schema: {},
            form: {},
            hidden: false,
            metadata: {},
            tags: [],
            topics: [],
            allow_any_kwargs: false
          },
          {
            name: 'say_json',
            display_name: 'say_json',
            description: 'Echos with JSON output_type',
            parameters: [
              {
                key: 'message',
                type: 'String',
                multi: false,
                display_name: 'message',
                optional: true,
                default: '{"str": "value", "nums": [1, 17], "obj": {"nested": "sweet"}}',
                description: 'The Message to be Echoed',
                nullable: false,
                type_info: {},
                parameters: []
              }
            ],
            command_type: 'ACTION',
            output_type: 'JSON',
            schema: {},
            form: {},
            hidden: false,
            metadata: {},
            tags: [],
            topics: [],
            allow_any_kwargs: false
          }
        ],
        icon_name: 'fa-comment',
        metadata: {},
        local: true,
        groups: [],
        requires: [],
        requires_timeout: 300,
      };

    return system;
}

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
        "command": "say",
        "status": "SUCCESS",

        "created_at": 1735585064780,
        "system": "echo",
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

function UnformattedInput(request: Request) {
    return (
      <div>
        <Message severity="warn" text="Unable to find source System/Command" />
        <pre>{JSON.stringify(request.parameters, null, 2)}</pre>
      </div>
        
    );
}

function RequestOptions(request: Request) {
    const items: MenuItem[] = [];

    if (request.status && ["CREATED","RECEIVED","IN_PROGRESS"].includes(request.status)) {
      items.push({
        label: 'Cancel Request',
            icon: <FontAwesomeIcon icon="xmark" />,
            command: () => {
                // 
            }
      });
    } else {
      items.push({
            label: 'Download Output',
            icon: <FontAwesomeIcon icon="download" />,
            command: () => {
                // 
            }
        });
      items.push({
        label: 'Delete Request',
            icon: <FontAwesomeIcon icon="xmark" />,
            command: () => {
                // 
            }
      });
    }

    const pourAgain = (request: Request) => {

    };

    return (
        <div className="card flex justify-content-end">
          <SplitButton 
            label="Pour Again" 
            icon={<FontAwesomeIcon icon="plus" />}
            model={items} 
            className="p-button-secondary" 
            onClick={() => pourAgain(request)} 
            severity="success"
            />
        </div>
    );
}

function RequestHeader(request: Request) {

    const iconItemTemplate = (item:any, options:any) => {
        
        if (item.icon) {
            return <span className={options.className}><FontAwesomeIcon icon={item.icon}/></span>;
        }
        return <span className={options.className}>{item.label}</span>;
        
    }

    const items = [
        {
            icon: "file-lines",
            template: iconItemTemplate
        },      
        {
            label: request.namespace,
            template: iconItemTemplate
        },
        {
            label: request.system,
            template: iconItemTemplate
        },
        {
            label: request.system_version,
            template: iconItemTemplate
        },
        {
            label: request.instance_name,
            template: iconItemTemplate
        },
        {
            label: request.command,
            template: iconItemTemplate
        },
        {
            label: request.id,
            template: iconItemTemplate
        }
    ];

    return (

            <BreadCrumb model={items} />

    )

}

function RequestView() {

    const { requestId } = useParams<{ requestId: string }>();
    const [request, setRequest] = useState<Request | null>(null);
    const [system, setSystem] = useState<System | null>(null);
    const [command, setCommand] = useState<any>(null);
    const [rootRequest, setRootRequest] = useState<Request | null>(null);

    function loadRootRequest(check_request: Request) {
        if (check_request.has_parent === true && check_request.parent && check_request.parent.id){
            GetRequest(check_request.parent.id, {}).then((root_request)=> {
                loadRootRequest(root_request);
            });
        } else {
            setRootRequest(check_request);
        }
    }

    useEffect(() => {
        if (!request) {
            GetRequest(requestId, {}).then((data: Request) => {
                setRequest(data);
            }).catch((error) => {
                console.error("Error fetching request:", error);
            });
        }
    }, []);

    

    useEffect(() => {
        if (request) {
            if (request.status && ["CANCELED","SUCCESS","ERROR","INVALID"].includes(request.status)){
              setActiveIndex(1);
            }

            loadRootRequest(request);

            const systems = GetSystemList({name: request.system, version: request.system_version, namespace: request.namespace, garden_name: request.target_garden}).then((data) => {
                if (data.length > 0) {
                    setSystem(data[0]);
                }
            }).catch((error) => {
                console.error("Error fetching system list:", error);
            });

            
        }
    }, [request]);

    useEffect(() => {
        if (system && system.commands && request) {
            const commandData = system.commands.find((cmd) => cmd.name === request.command);
            setCommand(commandData);
        }
      }, [system]);

    const stepperRef = useRef(null);
    const [activeIndex, setActiveIndex] = useState(0);

    return (<div>
        {request && <RequestHeader {...request} />}
        
        {rootRequest && <RequestTreeChart {...{rootRequest: rootRequest, currentRequestId: requestId}} />}
        
        {request && <Stepper ref={stepperRef} activeStep={activeIndex} style={{ flexBasis: '50rem' }}>
          <StepperPanel header="Request Parameters">
            <RequestOptions {...request} />
            {command && (<CommandForm {...{command: command, request:request}} />)}
            {!command && (<UnformattedInput {...request} />)}
          </StepperPanel>
          <StepperPanel header="Request Output">
            {request && <RequestOptions {...request} />}
            {request && <RequestOutput {...request} />}
          </StepperPanel>

        </Stepper>}
        
    </div>);
}

export default RequestView;
       
        