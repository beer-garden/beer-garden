import { Garden } from '../models/brewtils-types';
import { Config } from '../models/models';

export const GetGarden = async (garden_name: string, headerData?: any): Promise<Garden> => {
    try {
        const headers = new Headers();
        if (headerData) {
            for (const [key, value] of Object.entries(headerData)) {
                headers.append(key, value as string);
            }
        }

        const response = await fetch(`api/v1/garden/${garden_name}`, { headers: headers });
        if (!response.ok) {
            // Handle non-OK responses (e.g., 404, 500)
            throw new Error(`HTTP error: Status ${response.status}`);
        }
        const data = await response.json() as Garden;
        return data;
    } catch (error) {
        // Handle network errors or the error thrown above
        console.error("Error fetching Requests:", error);
        throw error; // Re-throw to be handled by the component/hook
    }
};

export const GetRootGarden = async (config: Config, headerData: any): Promise<Garden> => {
    return GetGarden(config.garden_name, headerData);
};

export const GetGardenList = async (headerData?: any): Promise<Array<Garden>> => {
    try {
        const headers = new Headers();
        if (headerData) {
            for (const [key, value] of Object.entries(headerData)) {
                headers.append(key, value as string);
            }
        }

        const response = await fetch(`api/v1/gardens/`, { headers: headers });
        if (!response.ok) {
            // Handle non-OK responses (e.g., 404, 500)
            throw new Error(`HTTP error: Status ${response.status}`);
        }
        const data = await response.json() as Array<Garden>;
        return data;
    } catch (error) {
        // Handle network errors or the error thrown above
        console.error("Error fetching Requests:", error);
        throw error; // Re-throw to be handled by the component/hook
    }
};