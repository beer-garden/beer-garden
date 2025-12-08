import { Request } from "./brewtils-types";
import { Fieldset } from 'primereact/fieldset';
function displautOutput(request: Request ) {
    if (request.output_type === "JSON") {

        let parsed_output = {};
        try {
            parsed_output = JSON.parse(request.output || '{}');
        } catch (e) {
            parsed_output = { error: 'Failed to parse JSON output' };
        }

        return (
            <pre>{JSON.stringify(parsed_output, null, 2)}</pre>
        );
    }

    if (request.output_type === "HTML") {
        return (
            <div dangerouslySetInnerHTML={{ __html: request.output || '' }}></div>
        );
    }

    if (request.output_type === "STRING") {
        return (
            <pre>{request.output}</pre>
        );
    } 

    if (request.output_type === "XML") {
        return (
            <pre>{request.output}</pre>
        );
    }

    if (request.output_type === "JS") {
        return (
            <pre>{request.output}</pre>
        );
    }

    if (request.output_type === "CSS") {
        return (
            <pre>{request.output}</pre>
        );
    }

    return (<div></div>);
}



function PrimeRequestOutput(request: Request) {

    

    return (
    <div>
        <Fieldset legend="Output">  
            {displautOutput(request)}
        </Fieldset>
    </div>);
}

export default PrimeRequestOutput;