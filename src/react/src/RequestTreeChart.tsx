import { TreeTable } from 'primereact/treetable';
import { Column } from 'primereact/column';
import { Request } from './brewtils-types';

function parseRequest(request: Request) {

    let item = {
        key: request.id,
            data: {
            command: request.command,
            status: request.status,
            namespace: request.namespace,
            system: request.system,
            system_version: request.system_version,
            instance_name: request.instance_name,
            created_at: new Date(request.created_at).toLocaleString(),
            status_updated_at: new Date(request.status_updated_at).toLocaleString(),
            updated_at: new Date(request.updated_at).toLocaleString(),
            comment: request.comment,
        },
        children: [] as Array<any>,
    };



  if (typeof request.children !== 'undefined' && request.children !== null && request.children.length > 0) {

    request.children.forEach((childRequest: Request) => {
        let child_item = parseRequest(childRequest);
        child_item.key = item.key + '-' + child_item.key;
        item.children.push(child_item);
    });
    
  }

  return item;
}

function RequestTreeChart(request: Request) {

    const node = parseRequest(request);


    return (
    <TreeTable value={[node]} tableStyle={{ minWidth: '50rem' }}>
        <Column field="command" header="Command" expander></Column>
        
        <Column field="status" header="status"></Column>
        <Column field="namespace" header="Namespace"></Column>
        <Column field="system" header="System"></Column>
        <Column field="system_version" header="System Version"></Column>
        <Column field="instance_name" header="Instance Name"></Column>

        <Column field="created_at" header="Created"></Column>
        <Column field="status_updated_at" header="Status Updated"></Column>
        <Column field="updated_at" header="Updated"></Column>
        <Column field="comment" header="Comment"></Column>
    </TreeTable>
    )
}

export default RequestTreeChart;