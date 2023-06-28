///////////////////////////////     GLOBAL VARIABLE DECLARATIONS     ///////////////////////////////

var CUR_CHAR = "";     // the current character's ASCII
var CUR_NAME = "";     // the current character's name
var CUR_NODES = [];    // order in the array corresponds to node index
var CUR_EDGES = {};    // key is the node-to-node pairing (e.g. "0-1" for node 0 to node 1) and value is the edge label





/////////////////////////////    FILE I/O FUNCTION DEFINITIONS     /////////////////////////////



// reads the text file and parses to nodes and edges
function readEntFile(){
    var file = document.getElementById("entFileIn").files[0];
    var reader = new FileReader();
    reader.readAsText(file);
    reader.onload = function(){
        try{
            // read in the graph
            graph_str = JSON.stringify(reader.result);

            // get the entity name
            CUR_NAME = file.name.split(".")[0].toUpperCase();  // get the name of the file without the extension

            // parse the graph
            importEntGraph(graph_str);

            // add the nodes and edges to the sidebar
            addCurGraphDivs();

        }catch(e){
            alert("Error parsing entity file! \nMake sure the file is a .txt file.");
            debug.innerHTML = e;
            return [];
        }
    }
}


// reads the entity text file data and parses to nodes and edges
function importEntGraph(graph_str){
    // clean up the string
    graph_str = graph_str.substring(1, graph_str.length-1)   //remove the quotes
    graph_str = graph_str.replace(/\\n/g, "\\n")
    let graph_lines = graph_str.split("\\n");

    // clear the current graph
    CUR_NODES = [];
    CUR_EDGES = {};

    // grab the start and ends of the nodes and edges definition lines
    let node_start = graph_lines.indexOf("-- NODES --");
    let edge_start = graph_lines.indexOf("-- EDGES --");

    // first line is the character ASCII
    CUR_CHAR = graph_lines[0].trim();

    // second set should be nodes
    for(let i = node_start+1; i < edge_start; i++){
        let node_line = graph_lines[i].trim();
        if(node_line == "")
            continue;
        
        // parse the line
        let node = node_line.split(":");
        let node_id = parseInt(node[0].trim());
        let node_label = node[1].trim();
        CUR_NODES[node_id] = node_label;
    }

    // third set should be edges
    for(let i = edge_start+1; i < graph_lines.length; i++){
        let edge_line = graph_lines[i].trim();
        if(edge_line == "")
            continue;

        // parse the line
        let edge = edge_line.split(":");
        let edge_pair = edge[0].trim();
        let edge_label = edge[1].trim();
        CUR_EDGES[edge_pair] = edge_label;
    }
}


// writes the current nodes and edges to a text file
// exports in the format specified by the amorphous fortress 1.0 framework 
function exportEntGraph(){
    // get the entity name
    let name = document.getElementById("name_in").value;
    if(name == ""){
        alert("Please enter an entity name to export!");
        DEBUG("Please enter an entity name to export!");
        return;
    }

    // get the entity ASCII
    let char = document.getElementById("char_in").value;
    if(char == ""){
        alert("Please enter an entity ASCII to export!");
        DEBUG("Please enter an entity ASCII to export!");
        return;
    }


    //////////   VALIDATION CHECKS   //////////

    if(CUR_NODES.length == 0){
        alert("Please add at least one node to the graph!");
        DEBUG("Please add at least one node to the graph!");
        return;
    }
    
    if(CUR_EDGES.length == 0){
        alert("Please add at least one edge to the graph!");
        DEBUG("Please add at least one edge to the graph!");
        return;
    }


    // create the graph string
    let graph_str = "";
    graph_str += `${char}\n`;
    graph_str += "-- NODES --\n";
    for(let i = 0; i < CUR_NODES.length; i++){
        let label = CUR_NODES[i];
        graph_str += `${i}: ${label}\n`;
    }
    graph_str += "-- EDGES --\n";
    for(let pair in CUR_EDGES){
        let label = CUR_EDGES[pair];
        graph_str += `${pair}: ${label}\n`;
    }

    // create the file
    var blob = new Blob([graph_str], {type: "text/plain;charset=utf-8"});
    saveAs(blob, `${name}.txt`);

}

// saves the blob as a file
function saveAs(blob, filename) {
    //make it a downloadable text
    let file = new Blob([blob], {type: 'text/plain'});
    if (window.navigator.msSaveOrOpenBlob) // IE10+
        window.navigator.msSaveOrOpenBlob(file, filename);
    else { // Others
        let a = document.createElement("a"),
        url = URL.createObjectURL(file);
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        //simultate clicking and downloading the link
        a.click();
        setTimeout(function() {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);  
        }, 0); 
    }
}


/////////////////////////////     HTML FUNCTION DEFINITIONS     /////////////////////////////



// adds the current nodes and edges to the sidebar
function addCurGraphDivs(){
    // clear the list
    let node_list = document.getElementById("node-list");
    let edge_list = document.getElementById("edge-list");
    node_list.innerHTML = "";
    edge_list.innerHTML = "";

    // set the entity name and ascii character
    document.getElementById("name_in").value = CUR_NAME;
    document.getElementById("name_txt").innerHTML = CUR_NAME;
    document.getElementById("char_in").value = CUR_CHAR;
    document.getElementById("char_txt").innerHTML = CUR_CHAR;

    // add the nodes
    for(let i = 0; i < CUR_NODES.length; i++){
        let label = CUR_NODES[i];
        addNodeItem(i, label);
    }

    // add the edges
    for(let pair in CUR_EDGES){
        let label = CUR_EDGES[pair];
        addEdgeItem(pair, label);
    }
}


// adds a node entry to the sidebar (try to add these in order)
function addNodeItem(node_id, label){
    // create the container div
    let node_div = document.createElement("div");
    node_div.className = "node-item";
    node_div.id = `node_${node_id}`;

    // create the node index
    let node_idx = document.createElement("div");
    node_idx.className = "node-index";
    node_idx.innerHTML = node_id;
    node_div.appendChild(node_idx);

    // create the node label
    let node_label = document.createElement("div");
    node_label.className = "node-label";
    node_label.innerHTML = label;
    node_div.appendChild(node_label);

    // add the div to the node list sidebar
    let node_list = document.getElementById("node-list");
    node_list.appendChild(node_div);
}


// adds an edge entry to the sidebar
function addEdgeItem(pair, label){
    // get the elements of the pair
    let pair_arr = pair.split("-");
    let node1 = pair_arr[0];
    let node2 = pair_arr[1];

    // create the container div
    let edge_div = document.createElement("div");
    edge_div.className = "edge-item";
    edge_div.id = `edge_${pair}`;

    // create the edge pair
    let edge_conn = document.createElement("div");
    edge_conn.className = "edge-conn";

    let edge_cs = document.createElement("div");
    edge_cs.className = "edge-s";
    edge_cs.innerHTML = node1;
    edge_conn.appendChild(edge_cs);

    let edge_ca = document.createElement("div");
    edge_ca.className = "edge-a";
    edge_ca.innerHTML = "->";
    edge_conn.appendChild(edge_ca);

    let edge_ce = document.createElement("div");
    edge_ce.className = "edge-e";
    edge_ce.innerHTML = node2;
    edge_conn.appendChild(edge_ce);

    edge_div.appendChild(edge_conn);

    // create the edge label
    let edge_label = document.createElement("div");
    edge_label.className = "edge-label";
    edge_label.innerHTML = label;
    edge_div.appendChild(edge_label);

    // add the div to the edge list sidebar
    let edge_list = document.getElementById("edge-list");
    edge_list.appendChild(edge_div);

}