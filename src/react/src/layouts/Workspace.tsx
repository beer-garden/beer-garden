import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { DataView } from "primereact/dataview";
import { useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { Card } from "primereact/card";
import RequestCreate from "../components/RequestCreate";
import { RequestCommand, RequestItem } from "../models/models";

function Workspace() {
  const [items, setItems] = useState<RequestItem[]>(() => {
    const saved = localStorage.getItem("requestItems");
    return saved ? JSON.parse(saved) : [];
  });

  const [sortAsc, setSortAsc] = useState(true);

  const [dataViewKey, setDataViewKey] = useState(0);

  useEffect(() => {
    localStorage.setItem("requestItems", JSON.stringify(items));
    setDataViewKey((prev) => prev + 1);
  }, [items]);

  const sortedItems = [...items].sort((a, b) =>
    sortAsc ? a.itemPos - b.itemPos : b.itemPos - a.itemPos,
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
    setItems(
      items.map((item) => (item.itemId === updated.itemId ? updated : item)),
    );
  };

  const deleteItem = (id: string) => {
    setItems(items.filter((item) => item.itemId !== id));
  };

  const listTemplate = (item: RequestItem[]) => {
    if (!items || items.length === 0) return null;

    const list = [] as Array<any>;

    items.forEach((value: RequestItem) => {
      if (value !== null && value !== undefined) {
        list.push(
          <Card
            key={value.itemId}
            className="flex mr-2 mb-2 mt-2"
            style={{ width: "45%"}}
            header={(<Button
              onClick={() => {
                deleteItem(value.itemId);
              }}
            >
              <FontAwesomeIcon icon="minus" />
            </Button>)}
            footer={(<div className="flex">
            <div>
              <Button
                label="Reset Form"
                severity="warning"
                icon="pi pi-arrow-right"
                //onClick={() => setResetForm(true)}
                className="mr-2"
              />
            </div>
            <div>
              {/* <CodeExample
                visibleCodeExample={visibleCodeExample}
                setVisibleCodeExample={setVisibleCodeExample}
                request={request}
              /> */}
              <Button
                label="Code Examples"
                severity="info"
                icon="pi pi-arrow-right"
                //onClick={() => setVisibleCodeExample(true)}
                className="mr-2"
              />
            </div>
            <div style={{ marginLeft: "auto" }}>
              
                <Button
                  label="Submit"
                  icon="pi pi-arrow-right"
                  onClick={() => {
                    //submitRequest();
                  }}
                />
              
              
            </div>
          </div>)}
          >
            
            
            {value.type === "REQUEST" && (
              <RequestCreate
                requestItem={value}
                updateRequestItem={updateItem}
              />
            )}
            
          </Card>,
        );
      }
    });

    return (<div className="flex grid grid-nogutter">{list}</div>);
  };

  
  return (
    <div>
      <h1>Workspace</h1>
      <Button onClick={() => addItem()}>
        <FontAwesomeIcon icon="file-pen" />
      </Button>
      {/* <ListTemplate items={items} /> */}
       <DataView  value={items} listTemplate={listTemplate} layout="grid" style={{height:"100%"}} /> 
    {/* <ReactGridLayout
      className="layout"
      layout={items.map((item, index) => ({
        x: (index % 2) * 6,
        y: Math.floor(index / 2) * 4,
        w: 6,
        h: 4,
        i: item.itemId,
      }))}
      // cols={12}
      // rowHeight={60}
      width={width}
    >
      {sortedItems.map((item) => (
        <div key={item.itemId} className="mb-2">
      <Card>
        <Button onClick={() => deleteItem(item.itemId)}>
          <FontAwesomeIcon icon="minus" />
        </Button>
        {item.type === "REQUEST" && (
          <RequestCreate
        requestItem={item}
        updateRequestItem={updateItem}
          />
        )}
      </Card>
        </div>
      ))}
    </ReactGridLayout> */}
    </div>
  );
}

export default Workspace;
