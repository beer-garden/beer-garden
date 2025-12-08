import React from 'react';
import { InputText } from 'primereact/inputtext';
import { InputNumber } from 'primereact/inputnumber';
import { Dropdown } from 'primereact/dropdown';
import { Checkbox } from 'primereact/checkbox';
import { Button } from 'primereact/button';
import { Command, Parameter } from './brewtils-types'; // Assuming this is the correct path
import { Fieldset } from 'primereact/fieldset';
import { Calendar } from 'primereact/calendar';
import { FileUpload } from 'primereact/fileupload';

function PrimeCommandForm (command: Command, enabled: boolean = false) {
    const [formData, setFormData] = React.useState<Record<string, any>>({});

    const handleChange = (name: string, value: any) => {
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        // onSubmit(formData);
    };

    const renderInputField = (parameter: Parameter) => {

        if (parameter.choices && parameter.choices.type === 'static' && parameter.choices.strict && Array.isArray(parameter.choices.value)) {
            const options = parameter.choices.value.map((choice) => ({
                label: choice,
                value: choice
            }));
            return (
                <div key={parameter.key} className="p-field">
                    <label htmlFor={parameter.key}>{parameter.key}</label>
                    <Dropdown
                        id={parameter.key}
                        value={parameter.default || ''}
                        options={options || []}
                        invalid={enabled && parameter.optional || undefined}
                        onChange={(e) => handleChange(e.target.id, e.value)}
                        placeholder={`Select ${parameter.key}`}
                    />
                </div>
            );
        }

        switch (parameter.type) {
            case 'String':
                return (
                    <div key={parameter.key} className="p-field">
                        <label htmlFor={parameter.key}>{parameter.key}</label>
                        <InputText
                            id={parameter.key}
                            value={parameter.default || ''}
                            invalid={enabled && parameter.optional || undefined}
                            onChange={(e) => handleChange(e.target.id, e.target.value)}
                        />
                    </div>
                );
            case 'Integer':
                return (
                    <div key={parameter.key} className="p-field">
                        <label htmlFor={parameter.key}>{parameter.key}</label>
                        <InputNumber
                            id={parameter.key}
                            type="number"
                            value={parameter.default || ''}
                            invalid={enabled && parameter.optional || undefined}
                            max={(parameter.maximum !== undefined) ? parameter.maximum : undefined}
                            min={(parameter.minimum !== undefined) ? parameter.minimum : undefined}
                            onValueChange={(e) => handleChange(e.target.id, e.target.value)}
                        />
                    </div>
                );
            case 'Float':
                return (
                    <div key={parameter.key} className="p-field">
                        <label htmlFor={parameter.key}>{parameter.key}</label>
                        <InputNumber
                            id={parameter.key}
                            type="number"
                            value={parameter.default || ''}
                            invalid={enabled && parameter.optional || undefined}
                            max={(parameter.maximum !== undefined) ? parameter.maximum : undefined}
                            min={(parameter.minimum !== undefined) ? parameter.minimum : undefined}
                            minFractionDigits={2}
                            onValueChange={(e) => handleChange(e.target.id, e.target.value)}
                        />
                    </div>
                );
            case 'Boolean':
                return (
                    <div key={parameter.key} className="p-field-checkbox">          
                        <label htmlFor={parameter.key}>{parameter.key}</label>
                        <Checkbox
                            inputId={parameter.key}
                            invalid={enabled && parameter.optional || undefined}
                            checked={parameter.default || false}
                            onChange={(e) => handleChange(e.target.id, e.checked)}
                        />
                    </div>
                );
            case 'Date':
                return (
                    <div key={parameter.key} className="p-field">
                        <label htmlFor={parameter.key}>{parameter.key}</label>
                        <Calendar
                            id={parameter.key}
                            value={parameter.default || ''}
                            invalid={enabled && parameter.optional || undefined}
                            hourFormat="24"
                            onChange={(e: any) => handleChange(e.target.id, e.value)}
                        />
                    </div>
                );
            case 'DateTime':
                return (
                    <div key={parameter.key} className="p-field">
                        <label htmlFor={parameter.key}>{parameter.key}</label>
                        <Calendar
                            id={parameter.key}
                            value={parameter.default || ''}
                            showTime
                            hourFormat="24"
                            invalid={enabled && parameter.optional || undefined}
                            onChange={(e: any) => handleChange(e.target.id, e.value)}                        
                        />
                    </div>
                );
            case 'Bytes':
                const customBytesUploader = async (event: any) => {
                    // convert file to bytes encoded
                    const file = event.files[0];
                    const reader = new FileReader();
                    let blob = await fetch(file.objectURL).then((r) => r.blob()); //blob:url
            
                    reader.readAsDataURL(blob);
            
                    reader.onloadend = function () {
                        const base64data = reader.result;
                        // Run Upload
                    };
                };
                return (
                    <div key={parameter.key} className="p-field">
                        <label htmlFor={parameter.key}>{parameter.key}</label>
                        <FileUpload id={parameter.key} mode="basic" customUpload uploadHandler={customBytesUploader} />
                    </div>
                );
            case 'Base64':
                const customBase64Uploader = async (event: any) => {
                    // convert file to base64 encoded
                    const file = event.files[0];
                    const reader = new FileReader();
                    let blob = await fetch(file.objectURL).then((r) => r.blob()); //blob:url
            
                    reader.readAsDataURL(blob);
            
                    reader.onloadend = function () {
                        const base64data = reader.result;
                        // Run Upload
                    };
                };
                return (
                    <div key={parameter.key} className="p-field">
                        <label htmlFor={parameter.key}>{parameter.key}</label>
                        <FileUpload id={parameter.key} mode="basic" customUpload uploadHandler={customBase64Uploader} />
                    </div>
                );
            // case 'Enum':
            //     return (
            //         <div key={key} className="p-field">
            //             <label htmlFor={key}>{key}</label>
            //             <Dropdown
            //                 id={key}
            //                 value={formData[key] || defaultValue || ''}
            //                 options={options || []}
            //                 onChange={(e) => handleChange(e.target.id, e.value)}
            //                 placeholder={`Select ${key}`}
            //             />
            //         </div>
            //     );
            default:
                return null;
        }
    };

    return (
        <Fieldset legend="Input">  
        <form onSubmit={handleSubmit}>
            {command.parameters?.map((parameter) => renderInputField(parameter))}
            {enabled && (<Button type="submit" label="Submit" />)}
            
        </form>
        </Fieldset>
    );
};

export default PrimeCommandForm;