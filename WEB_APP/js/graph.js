///////////////////////////////     GLOBAL VARIABLE DECLARATIONS     ///////////////////////////////

/// graph definitions ///
var CUR_CHAR = "";     // the current character's ASCII
var CUR_NAME = "";     // the current character's name
var CUR_NODES = [];    // order in the array corresponds to node index
var CUR_EDGES = {};    // key is the node-to-node pairing (e.g. "0-1" for node 0 to node 1) and value is the edge label

// renderer definitions ///
var graph_canvas = document.getElementById("graph-canvas");
graph_canvas.width = 615;
graph_canvas.height = 625;
var gctx = graph_canvas.getContext("2d");


/////////////////////////////   GENERIC FUNCTIONS     /////////////////////////////

// draws a debug point
function debugPoint(p, c='blue', s=5){
    gctx.fillStyle = c;
    gctx.fillRect(p.x-Math.floor(s/2), p.y-Math.floor(s/2), s, s);
    gctx.fillStyle = "black";
}

// get the opposite edge
function oppEdge(edge){
    let es = edge.split("-");
    return `${es[1]}-${es[0]}`;
}
//////////////////////////   MATH BULLSHIT FUNCTIONS     /////////////////////////

// radians to degrees converter
function rad2deg(rad){
    return rad * (180/Math.PI);
}

// degrees to radians converter
function deg2rad(deg){
    return deg * (Math.PI/180);
}

// returns the slope of the line between two points
function getSlope(a,b){
    return (b.y - a.y) / (b.x - a.x);
}

// returns the distance between two points
function dist(a,b){
    return Math.sqrt(Math.pow(b.x-a.x,2) + Math.pow(b.y-a.y,2));
}

// calculates the perpendicular bisectors of two points
// for use with the edge quadratic curve
function getPerpBisectors(a,b,d=null){
    // 1. get the slope of ab
    let slope = getSlope(a,b);

    // 2. get the midpoint of ab
    let mid = {
        x: (a.x + b.x) / 2,
        y: (a.y + b.y) / 2
    }

    // 3. get the perpendicular slope
    let perp_slope = null;
    if(slope == 0){
        perp_slope = Infinity;
    }else if(slope == Infinity){
        perp_slope = 0;
    }else{
        perp_slope = -1/slope;
    }

    // 4. find the alternative points based on the cos/sin right angle triangle
    d = d == null ? dist(a,mid)/2 : d;  //distance between a and mid
    let ang = Math.atan(perp_slope);  // angle between the perpendicular bisector slope and the x-axis
    let dx = d*Math.cos(ang);   
    let dy = d*Math.sin(ang);

    let alt_points = [
        {x:mid.x+dx, y:mid.y+dy},
        {x:mid.x-dx, y:mid.y-dy}
    ]
    return alt_points;
}

/////////////////////////////    FILE I/O FUNCTIONS     /////////////////////////////



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

            // redraw the graph
            makeNodes();
            makeEdges();

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


// clear the current graph
function newGraph(){
    if(confirm("Are you sure you want to create a new graph? Any unsaved changes to the current one will be lost.") == false)
        return;

    CUR_NAME = "";
    CUR_CHAR = "";
    CUR_NODES = [];
    CUR_EDGES = {};
    addCurGraphDivs();
}


/////////////////////////////    GRAPH CANVAS FUNCTIONS AND DEFINITIONS    /////////////////////////////



// define the node class for rendering
class CANV_NODE {
    constructor(x, y, label, idx) {
        this.x = x;          // x position
        this.y = y;          // y position
        this.r = 40;         //radius of the circle
        this.fs = 24;        //font size
        this.label = label;  //label of the node inside the circle
        this.idx = idx;      //index of the node in the graph
    }
}

class CANV_EDGE{
    constructor(n1,n2, angle, double, label){
        this.n1 = n1;       // node 1
        this.n2 = n2;       // node 2
        this.angle = angle; // angle between nodes 1 and 2
        this.label = label; // label of the edge
        this.double_edge = double; // whether or not this edge is a double edge
        this.edge_key = `${n1.idx}-${n2.idx}`; // key for the edge
    }
}



let G_NODES = [];   // list of graph visualizer nodes
let G_EDGES = [];   // list of graph visualizer edges

// arranges the current nodes in a clockwise circle
function makeNodes(){
    // define graph properties
    let num_nodes = CUR_NODES.length;
    let r = Math.min(250,120 + (Math.max(num_nodes,4) * 10));
    let cx = graph_canvas.width/2;
    let cy = graph_canvas.height/2;
    
    // arrange the nodes in a circle
    G_NODES = [];
    for(let i = 0; i < num_nodes; i++){
        let angle = (i/num_nodes) * 2 * Math.PI;
        let x = cx;
        let y = cy;
        if(num_nodes > 1){
            x = cx + r * Math.cos(angle);
            y = cy + r * Math.sin(angle);
        }
        let label = CUR_NODES[i];
        G_NODES.push(new CANV_NODE(x, y, label, i));
    }
}

// connects the edges between the nodes
function makeEdges(){
    // clear the edges
    G_EDGES = [];

    // connect the edges
    let e = []
    let all_pairs = Object.keys(CUR_EDGES);
    for(let pair in CUR_EDGES){

        let label = CUR_EDGES[pair];

        let nodes = pair.split("-");
        let n1 = G_NODES[parseInt(nodes[0])];
        let n2 = G_NODES[parseInt(nodes[1])];
        let angle = Math.atan2(n2.y - n1.y, n2.x - n1.x);

        let alt_edge = oppEdge(pair);
        let double_edged = (all_pairs.indexOf(alt_edge) != -1);

        G_EDGES.push(new CANV_EDGE(n1,n2,angle,double_edged,label));
        // e.push(`(${pair})[${label}] -> ${angle.toFixed(2)}(r)==${Math.round(rad2deg(angle))}(d)`)
        // e.push(`(${pair})[${label}] -> ${double_edged} => ${alt_edge}`)
    }
    // DEBUG(e);

}


// draw each node in the graph
function drawNodes(){
    // draw the nodes
    for(let i = 0; i < G_NODES.length; i++){
        let node = G_NODES[i];

        //fill the circle
        gctx.fillStyle = "aliceblue"
        gctx.beginPath();
        gctx.arc(node.x, node.y, node.r, 0, 2 * Math.PI);
        gctx.fill();

        //draw the circle
        gctx.strokeStyle = "#000000";
        gctx.fillStyle = "#000";
        gctx.beginPath();
        gctx.arc(node.x, node.y, node.r, 0, 2 * Math.PI);
        gctx.stroke();

        //add the label
        gctx.font = node.fs + "px Proggy";
        gctx.textAlign = "center";
        gctx.fillText(node.label, node.x, node.y+(node.fs/4));

        //add the index (outside)
        gctx.font = "20px monospace";
        gctx.textAlign = "center";
        gctx.fillText(i, node.x-node.r, node.y-node.r);
    }
}


// draw each edge in the graph
function drawEdges(){
    //draw the edges
    let ang = [];
    let de = [];
    for(let i = 0; i < G_EDGES.length; i++){
        let edge = G_EDGES[i];

        //get the line points between the two nodes
        let x1 = edge.n1.x;
        let y1 = edge.n1.y;
        let x2 = edge.n2.x;
        let y2 = edge.n2.y;

        let estr = edge.edge_key;

        //draw the line
        gctx.beginPath();
        gctx.moveTo(x1,y1);
        if(edge.double_edge){
            let alt_pts = getPerpBisectors(edge.n1,edge.n2);
            let ei = (de.indexOf(oppEdge(estr)) == -1) ? 0 : 1;
            gctx.quadraticCurveTo(alt_pts[ei].x, alt_pts[ei].y, x2, y2)   //need to get perpendicular line to pull the quadratic curve to
            de.push(estr);
        }else
            gctx.lineTo(x2,y2);
        gctx.stroke();

        //add the label (with rotation if needed)å
        let mid_x = (x1+x2)/2;
        let mid_y = (y1+y2)/2;
        gctx.font = "20px monospace";
        gctx.textAlign = "center";
        gctx.save();
        gctx.translate(mid_x, mid_y);
        let abs_angle = Math.abs(edge.angle)
        if(abs_angle < 2){
            gctx.rotate(edge.angle);
        }else{
            gctx.rotate(edge.angle + Math.PI);
        }
        gctx.fillText(edge.label, 0, (edge.double_edge ? -14 : -7));
        gctx.restore();

    }
}


// render the graph canvas
function renderGraph(){
    // clear the canvas
    gctx.clearRect(0, 0, graph_canvas.width, graph_canvas.height);

    //draw the graph
    drawEdges();
    drawNodes();
   
}