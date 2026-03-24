import { RequestCommand, RequestItem } from "../models/models";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { useEffect, useState } from "react";
import  RequestCreate from "../components/RequestCreate";
import { v4 as uuidv4 } from "uuid";
import { DataView } from "primereact/dataview";

function Workspace() {

    const [items, setItems] = useState<RequestItem[]>(() => {
        const saved = localStorage.getItem('requestItems');
        return saved ? JSON.parse(saved) : [];
    });

    const [sortAsc, setSortAsc] = useState(true);

    useEffect(() => {
        localStorage.setItem('requestItems', JSON.stringify(items));
    }, [items]);

    const sortedItems = [...items].sort((a, b) => 
        sortAsc ? a.itemPos - b.itemPos : b.itemPos - a.itemPos
    );

    const addItem = () => {
        const newItem: RequestItem = {
            itemId: uuidv4(),
            itemPos: items.length + 1,
            type: "REQUEST",
        };
        setItems([...items, newItem]);
    };

    const updateItem = (updated: RequestItem) => {
        setItems(items.map(item => item.itemId === updated.itemId ? updated : item));
    };

    const deleteItem = (id: string) => {
        setItems(items.filter(item => item.itemId !== id));
    };

    const RequestTemplate = (value: RequestItem) => {
    if (value.type === "REQUEST") {
      return (
        <RequestCreate
          requestItem={value}
            updateRequestItem={updateItem}
        />
      );    
    } 
    return <div>ERROR</div>;
  };

  const listTemplate = (items: any) => {
      if (!items || items.length === 0) return null;
  
      const list = [] as Array<any>;
  
      items.forEach((value: RequestItem) => {
        if (value !== null && value !== undefined) {
          list.push(
            <div key={value.itemId} className="mr-2 mb-2" style={{width: "45%"}}>
              <Button
                onClick={() => {
                  deleteItem(value.itemId);
                }}
              >
                <FontAwesomeIcon icon="minus" />
              </Button>
              {value.type === "REQUEST" && (<RequestCreate
                requestItem={value}
                    updateRequestItem={updateItem}
                />)}
            </div>,
          );
        }
      });
  
      return <div className="grid grid-nogutter">{list}</div>;
    };
  return (
    <div>
      <h1>Workspace</h1>
      <Button onClick={() => addItem()}>
              <FontAwesomeIcon icon="file-pen" />
            </Button>
      <DataView value={items} listTemplate={listTemplate} />
    </div>
  );
}

export default Workspace;