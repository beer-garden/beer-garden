import * as SparkMD5 from "spark-md5";

import { GetAuthHeaders } from "./token_service";
import { GetBaseURL } from "./util_service";

const chunkSize = 255 * 1024;

export const calculateMD5 = async (file: File): Promise<string | null> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      if (
        event !== null &&
        event.target !== null &&
        event.target.result !== null
      ) {
        const arrayBuffer = event.target.result;
        const spark = new SparkMD5.ArrayBuffer();
        spark.append(arrayBuffer);
        const md5Sum = spark.end();
        resolve(md5Sum);
      } else {
        resolve(null);
      }
    };

    reader.onerror = () => {
      reject(new Error(`Failed to calculate MD5: ${reader.error}`));
    };

    reader.readAsArrayBuffer(file);
  });
};

export const uploadFile = async (
  file: File,
  setPercentage: (percentage: number) => void,
  headerData?: any,
) => {
  const headers = GetAuthHeaders();

  for (const [key, value] of Object.entries(headerData || {})) {
    headers.append(key, value as string);
  }

  //   const numChunks = Math.ceil(file.size / chunkSize);

  const md5_sum = await calculateMD5(file);
  const response = await fetch(
    `${GetBaseURL()}/api/vbeta/chunks/id/?file_name=${encodeURIComponent(file.name)}&file_size=${file.size}&chunk_size=${chunkSize}&md5_sum=${md5_sum}`,
    {
      headers: headers,
    },
  );

  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }

  const data = await response.json();
  const fileId = data["details"]["file_id"];

  if (!fileId || !data["details"]["operation_complete"]) {
    throw new Error(
      `File upload failed; could not retrieve a FileID for upload, message: ${data["details"]["message"]}`,
    );
  }

  headers.append("Content-Type", "application/json");
  for (let offset = 0; offset < file.size; offset += chunkSize) {
    await uploadChunk(file, fileId, offset, setPercentage);
  }

  await verifyFile(fileId);

  return data;
};

export const uploadChunk = async (
  file: File,
  fileId: string,
  offset: number,
  setPercentage: (percentage: number) => void,
) => {
  return await new Promise((resolve, reject) => {
    const chunk = file.slice(
      offset * chunkSize,
      offset * chunkSize + chunkSize,
    );
    const reader = new FileReader();
    reader.onload = (e) => {
      if (e === null || e.target === null || e.target.result === null) {
        reject(new Error("Failed to read file chunk"));
      } else {
        const result = e.target.result as string;
        const headers = GetAuthHeaders();
        headers.append("Content-Type", "application/json");

        fetch(`${GetBaseURL()}/api/vbeta/chunks/?file_id=${fileId}`, {
          method: "POST",
          headers: headers,
          body: JSON.stringify({ data: result.split(",")[1], offset: offset }),
        })
          .then((chunkResponse) => {
            if (!chunkResponse.ok) {
              reject(new Error(`HTTP error: Status ${chunkResponse.status}`));
            } else {
              setPercentage(Math.floor((offset / file.size) * 100));
              resolve(chunkResponse);
            }
          })
          .catch((error) => {
            reject(new Error(`Network error: ${error}`));
          });
      }
    };
    reader.onerror = () => {
      reject(new Error("Failed to read file chunk"));
    };
    reader.readAsDataURL(chunk);
  });
};

export const verifyFile = async (fileId: string) => {
  const response = await fetch(
    `${GetBaseURL()}/api/vbeta/chunks?file_id=${fileId}&verify=true`,
  );
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }

  const data = await response.json();
  return data["message"];
};

export const removeFile = async (fileId: string) => {
  const response = await fetch(
    `${GetBaseURL()}/api/vbeta/chunks/?file_id=${fileId}`,
    {
      method: "DELETE",
    },
  );
  if (!response.ok) {
    // Handle non-OK responses (e.g., 404, 500)
    throw new Error(`HTTP error: Status ${response.status}`);
  }

  return true;
};
