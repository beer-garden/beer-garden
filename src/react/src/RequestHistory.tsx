import { Request } from './brewtils-types';
import { TreeTable } from 'primereact/treetable';
import { Column } from 'primereact/column';

// https://primereact.org/treetable/

function flattenRequests(request: Request, data: Array<Request>) {

  data = [{
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
    "command_display_name": "sleep_say",
    "comment": ""
  },
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
    "parent_id": "6772ed28aa78c5898091e9e7",
    "command_display_name": "sleep",
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
    "parent_id": "6772ed28aa78c5898091e9e7",

    "command_display_name": "say",
  }
  ];
  return data;
}
function RequestHistory(request: Request) {

  let data = flattenRequests(request, []);

  if (data.length > 0) {
    return (
      <div>
        <TreeTable value={data} tableStyle={{ minWidth: '50rem' }}>
          <Column field="command" header="Command" expander></Column>
          <Column field="status" header="Status"></Column>
        </TreeTable>
      </div>
    )
  }
  return (<div></div>);

}

export default RequestHistory;