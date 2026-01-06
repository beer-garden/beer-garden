import { Request } from '../models/brewtils-types';
import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { GetRequestList } from '../services/request_service';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { FilterMatchMode } from 'primereact/api';
import { Calendar } from 'primereact/calendar'
import { MultiSelect } from 'primereact/multiselect';
import { Button } from 'primereact/button';

import { useLocation } from 'react-router-dom';

function RequestIndex() {

    const [requests, setRequests] =  useState<Array<Request>>([]);
    const [loading, setLoading] = useState(false);
    const [totalRecords, setTotalRecords] = useState(0);
    const [lazyParams, setLazyParams] = useState({ first: 0, rows: 10, page: 0 });
    let location = useLocation();

    const [filters, setFilters] = useState({
        command_display_name: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
        namespace: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
        system: { value: null, matchMode: FilterMatchMode.STARTS_WITH},
        system_version: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
        instance_name: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
        status: { value: null, matchMode: FilterMatchMode.IN},
        created_at: { value: null, matchMode: FilterMatchMode.DATE_IS },
        comment: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    });

    
 
    const generateFilterQuery = () => {

        let filterQuery: Record<string, any> = {};

        Object.entries(filters).forEach(([field, filterMeta]) => {

            if (field === null || field === undefined) {
                return;
            }

            filterQuery['include'] = filterQuery['include'] || ['id'];
            filterQuery['include'].push(field);

            if (filterMeta.value === null || filterMeta.value === undefined || filterMeta.value === '') {
                return;
            }

            filterQuery['query'] = filterQuery['query'] || [];

            let filter: Record<string, any> = { field_name: field, modifier: "", value: filterMeta.value }

            if (filterMeta.matchMode === FilterMatchMode.STARTS_WITH) {
                filter['modifier'] = 'startswith';
            } else if (filterMeta.matchMode === FilterMatchMode.ENDS_WITH) {
                filter['modifier'] = 'endswith';
            } else if (filterMeta.matchMode === FilterMatchMode.EQUALS) {
                // Skip          
            } else if (filterMeta.matchMode === FilterMatchMode.NOT_EQUALS) {
                filter['modifier'] = 'ne';
            } else if (filterMeta.matchMode === FilterMatchMode.CONTAINS) {
                filter['modifier'] = 'contains';
            } else if (filterMeta.matchMode === FilterMatchMode.NOT_CONTAINS) {
                filter['modifier'] = 'not__contains';
            } else if (filterMeta.matchMode === FilterMatchMode.LESS_THAN) {
                filter['modifier'] = 'lt';
            } else if (filterMeta.matchMode === FilterMatchMode.LESS_THAN_OR_EQUAL_TO) {
                filter['modifier'] = 'lte';
            } else if (filterMeta.matchMode === FilterMatchMode.GREATER_THAN) {
                filter['modifier'] = 'gt';
            } else if (filterMeta.matchMode === FilterMatchMode.GREATER_THAN_OR_EQUAL_TO) {
                filter['modifier'] = 'gte';
            } else if (filterMeta.matchMode === FilterMatchMode.DATE_IS) {
                filter['value'] = (filterMeta.value as Date).toISOString().substring(0, 19).replace('T', ' ');
            } else if (filterMeta.matchMode === FilterMatchMode.DATE_IS_NOT) {
                filter['modifier'] = 'ne';
                filter['value'] = (filterMeta.value as Date).toISOString().substring(0, 19).replace('T', ' ');
            } else if (filterMeta.matchMode === FilterMatchMode.DATE_AFTER) {
                filter['modifier'] = 'gt';
                filter['value'] = (filterMeta.value as Date).toISOString().substring(0, 19).replace('T', ' ');
            } else if (filterMeta.matchMode === FilterMatchMode.DATE_BEFORE) {
                filter['modifier'] = 'lt';
                filter['value'] = (filterMeta.value as Date).toISOString().substring(0, 19).replace('T', ' ');
            } else if (filterMeta.matchMode === FilterMatchMode.IN) {
                filter['modifier'] = 'in';
                filter['value'] = (filterMeta.value as Array<any>).map((item) => item['name'])
            } else if (filterMeta.matchMode === FilterMatchMode.NOT_IN) {
                filter['modifier'] = 'nin';
                filter['value'] = (filterMeta.value as Array<any>).map((item) => item['name'])
            } else {
                // Not Defined yet
            }

            filterQuery['query'].push(JSON.stringify(filter))

        });

        return filterQuery;
    }

    const lazyLoadData = () => {
        setLoading(true);

        const queryHeaders = {
            'length': lazyParams.rows,
            'start': lazyParams.first,
            ...generateFilterQuery()
        };
        
        GetRequestList(queryHeaders).then((data: [Array<Request>, Headers]) => {
            const [requests, headers] = data;

            setRequests(requests);

            if (headers.has('Recordstotal')) {
                setTotalRecords(parseInt(headers.get('Recordstotal') || '0', 10));
            } else {
                setTotalRecords(requests.length);
            }
            setLoading(false);
        });
    };

    useEffect(() => {
        lazyLoadData();
    }, [lazyParams, filters]);

    const onPage = (event: any) => {
        setLazyParams(event);
    };

    const formatDate = (value: string) => {
        const date = new Date(value);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    const dateTimeFilterTemplate = (options: any) => {
        return (
            <Calendar
                value={options.value}
                onChange={(e) => options.filterCallback(e.value, options.index)}
                dateFormat="mm/dd/yy"
                showTime
                hourFormat="24" // or "12"
                placeholder="MM/DD/YYYY HH:MM"
                mask="99/99/9999 99:99"
            />
        );
    }

    const statuses = [
        { name: 'CREATED' },
        { name: 'RECEIVED'},
        { name: 'IN_PROGRESS'},
        { name: 'CANCELED' },
        { name: 'SUCCESS' },
        { name: 'ERROR' },
        { name: 'INVALID' },
    ];

    const statusFilterTemplate = (options: any) => {
        return (
            <MultiSelect value={options.value} onChange={(e) => options.filterCallback(e.value, options.index)} options={statuses} optionLabel="name" 
                placeholder="Status" className="w-full md:w-20rem" />
        );
    }

    const header = (
        <div className="flex flex-wrap align-items-center justify-content-between gap-2">
            <span className="text-xl text-900 font-bold">Requests</span>
            <Button rounded raised onClick={lazyLoadData}><FontAwesomeIcon icon="refresh" /> </Button>
        </div>
    );

    const commandNameTemplate = (request: Request) => {
        return <div><Button rounded raised link onClick={() => window.open('/request/' + request.id, '_self')} ><FontAwesomeIcon icon="arrow-up-right-from-square" /> </Button> {request.command_display_name}</div>;
    };

    return (
        <div>
            <DataTable
                value={requests}
                loading={loading}
                lazy
                paginator
                header={header}
                rows={lazyParams.rows}
                first={lazyParams.first}
                totalRecords={totalRecords}
                onPage={onPage}
                filters={filters}
                onFilter={(e) => setFilters(e.filters as typeof filters)}
                rowsPerPageOptions={[5, 10, 20, 50]}
            >
                <Column field="command_display_name" filter header="Command" body={commandNameTemplate} />
                <Column field="namespace" filter header="Namespace" />
                <Column field="system" filter header="System" />
                <Column field="system_version" filter header="Version" />       
                <Column field="instance_name" filter header="Instance" />
                <Column field="status" filter header="Status" filterElement={statusFilterTemplate} filterMatchModeOptions={[{label: 'In', value: FilterMatchMode.IN}, {label: 'Not In', value: FilterMatchMode.NOT_IN}]} />
                <Column field="created_at" filter dataType="date" header="Created" body={(rowData)=> formatDate(rowData.created_at)} filterElement={dateTimeFilterTemplate}/>
                <Column field="comment" filter header="Comment" />
            </DataTable>
        </div>
    );

}

export default RequestIndex;
