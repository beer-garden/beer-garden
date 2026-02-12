export const ClearAllQueues = async (gardenName?: string): Promise<void> => {
  try {
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    let fetch_url = "api/v1/queues";
    if (gardenName) {
      headers.append("Target-Garden", gardenName);
      fetch_url = "api/v1/queues?garden_name=" + encodeURIComponent(gardenName);
    }
    const response = await fetch(fetch_url, {
      headers: headers,
      method: "DELETE",
    });
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
  } catch (error) {
    // Handle network errors or the error thrown above
    throw error; // Re-throw to be handled by the component/hook
  }
};
