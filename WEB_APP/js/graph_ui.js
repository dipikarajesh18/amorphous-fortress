/*
 * GRAPH_UI.JS
 * Code for the graph canvas interactive UI (left section of the screen)
 * Written by: Milk + Dipika + Github Copilot
*/



///////////////////////////////     GLOBAL VARIABLE DECLARATIONS     ///////////////////////////////

/// graph definitions ///
var CUR_CHAR = "";     // the current character's ASCII
var CUR_NAME = "";     // the current character's name
var CUR_NODES = [];    // order in the array corresponds to node index
var CUR_EDGES = {};    // key is the node-to-node pairing (e.g. "0-1" for node 0 to node 1) and value is the edge label

// canvas definitions ///
var graph_canvas = document.getElementById("graph-canvas");
graph_canvas.width = 615;
graph_canvas.height = 625;
var gctx = graph_canvas.getContext("2d");

var HIGHLIGHT_COLOR = "#00B6FF";  
var SELECT_COLOR = "#00EC16";
var DRAG_COLOR = "#FFD200";

var graph_bound = graph_canvas.getBoundingClientRect();
var cur_drag_node  = null;
var cur_selection = null;   // can be a node or an edge
var mouse_pos = {x:0, y:0};



/////////////////////////////   GENERIC FUNCTIONS     /////////////////////////////

// get the opposite edge
function oppEdge(edge){
    let es = edge.split("-");
    return `${es[1]}-${es[0]}`;
}

// draws a debug point
function debugPoint(p, c='blue', s=5){
    gctx.fillStyle = c;
    gctx.fillRect(p.x-Math.floor(s/2), p.y-Math.floor(s/2), s, s);
    gctx.fillStyle = "black";
}

// draws a polygon given an array of points to move to
function debugPoly(poly, c='blue'){
    if(poly.length < 2) return;

    gctx.strokeStyle = c;
    gctx.beginPath();
    gctx.moveTo(poly[0].x, poly[0].y);
    for(let i = 1; i < poly.length; i++){
        gctx.lineTo(poly[i].x, poly[i].y);
    }
    gctx.closePath();
    gctx.stroke();
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

// check if 2 line segments intersect
// a = [p1,p2], b = [p3,p4]
function crosses(a,b){
    return ccw(a[0],b[0],b[1]) != ccw(a[1],b[0],b[1]) && ccw(a[0],a[1],b[0]) != ccw(a[0],a[1],b[1]);
}

// idfk copilot wrote this
function ccw(a,b,c){
    return (c.y-a.y)*(b.x-a.x) > (b.y-a.y)*(c.x-a.x);
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
        this.x = x;                 // x position
        this.y = y;                 // y position
        this.r = 40;                //radius of the circle
        this.canv_angle = 0;        //angle of the node on the canvas relative to the central circle
        this.fs = 24;               //font size
        this.label = label;         //label of the node inside the circle
        this.idx = idx;             //index of the node in the graph
        this.highlight = false;     //whether or not the node is highlighted
        this.select = false;        //whether or not the node is selected
    }
}

// define the edge class for rendering
class CANV_EDGE{
    constructor(n1,n2, angle, double, label){
        this.n1 = n1;                            // node 1
        this.n2 = n2;                            // node 2
        this.angle = angle;                      // angle of the edge
        this.label = label;                      // label of the edge
        this.double_edge = double;               // whether or not this edge is a double edge
        this.edge_key = `${n1.idx}-${n2.idx}`;   // key for the edge label (node1-node2)
        this.invis_pt = {x:0,y:0};               // invisible point for rendering - pulls the quadratic curve edge line
        this.label_dist = 14;                    // distance of label away from the edge
        this.highlight = false;                  // whether or not the edge is highlighted
        this.select = false;                     // whether or not the edge is selected
    }

    // somewhat hacky way of creating a bounding box for the edge
    make_bound_box(vd,double){

        //for self-loops, just make a square around the center node
        if(this.n1.idx == this.n2.idx){
            let x = this.invis_pt.x;
            let y = this.invis_pt.y;
            let r = this.n1.r*(2/3);

            let bbox = [
                {x:x-r, y:y-r},
                {x:x+r, y:y-r},
                {x:x+r, y:y+r},
                {x:x-r, y:y+r}
            ]
            this.bbox = bbox;
            return;
        }

        // vd = vertical distance
        let x1 = this.n1.x;
        let y1 = this.n1.y;
        let x2 = this.n2.x;
        let y2 = this.n2.y;
        let mdpt = {x:(x1+x2)/2, y:(y1+y2)/2};

        // get perpendicular angle
        let perp_angle = Math.atan2(y2-y1, x2-x1) + Math.PI/2;

        // create the points offset by the right angle perpendicular to the edge
        let new_point_1 = {x:x1+vd*Math.cos(perp_angle), y:y1+vd*Math.sin(perp_angle)};
        let new_point_2 = {x:x1-vd*Math.cos(perp_angle), y:y1-vd*Math.sin(perp_angle)};
        let new_point_3 = {x:x2+vd*Math.cos(perp_angle), y:y2+vd*Math.sin(perp_angle)};
        let new_point_4 = {x:x2-vd*Math.cos(perp_angle), y:y2-vd*Math.sin(perp_angle)};

        let bbox = [new_point_1, new_point_3, new_point_4, new_point_2];

        // shift the points if it's a double edge
        // TODO: this is technically wrong but it works (the overlap is incorrect ssshhhhhhh)
        if(double){
            //sort by the 2 closest points
            let bbox_i = [];
            for(let i =0;i<4;i++){
                bbox_i[i] = {'i':i, 'd':dist(bbox[i], this.invis_pt), 'pt':bbox[i]};
            }
            bbox_i.sort(function(a,b){return a['d']-b['d']});

            let perp_angle = Math.atan2(mdpt.y-this.invis_pt.y, mdpt.x-this.invis_pt.x);

            // shift the 2 closest points
            for(let i = 0; i < 2; i++){
                let pt = bbox_i[i]['pt'];
                pt.x = pt.x - Math.cos(perp_angle) * this.invis_pt_d*(2/3);
                pt.y = pt.y - Math.sin(perp_angle) * this.invis_pt_d*(2/3);
                bbox[bbox_i['i']] = pt;
            }
            for(let i = 2; i < 4; i++){
                let pt = bbox_i[i]['pt'];
                pt.x = pt.x - Math.cos(perp_angle) * this.invis_pt_d/3;
                pt.y = pt.y - Math.sin(perp_angle) * this.invis_pt_d/3;
                bbox[bbox_i['i']] = pt;
            }
        }

        //shrink to offset the node radius
        let r = this.n1.r;
        for(let i = 0; i < 4; i++){
            let a = Math.atan2(bbox[i].y-mdpt.y, bbox[i].x-mdpt.x);
            bbox[i].x = bbox[i].x - r*Math.cos(a);
            bbox[i].y = bbox[i].y - r*Math.sin(a);
        }


        this.bbox = bbox;
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

    let offset_angle = -90;
    
    // arrange the nodes in a circle
    G_NODES = [];
    for(let i = 0; i < num_nodes; i++){
        let angle = (i/num_nodes) * 2 * Math.PI;
        let x = cx;
        let y = cy;
        if(num_nodes > 1){
            x = cx + r * Math.cos(angle+deg2rad(offset_angle));
            y = cy + r * Math.sin(angle+deg2rad(offset_angle));
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
        let double_edged = (all_pairs.indexOf(alt_edge) != -1 && alt_edge != pair);

        let new_g_edge = new CANV_EDGE(n1,n2,angle,double_edged,label)

        G_EDGES.push(new_g_edge);

        // e.push(`(${pair})[${label}] -> ${angle.toFixed(2)}(r)==${Math.round(rad2deg(angle))}(d)`)
        // e.push(`(${pair})[${label}] -> ${double_edged} => ${alt_edge}`)

    }
    // DEBUG(e);

}


/////////////////////////////    RENDER FUNCTIONS    /////////////////////////////


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
        if(cur_drag_node && cur_drag_node.idx == node.idx && cur_drag_node.drag){
            gctx.strokeStyle = DRAG_COLOR;
            gctx.lineWidth = 4;
        }
        else if(node.select){
            gctx.strokeStyle = SELECT_COLOR;
            gctx.lineWidth = 4;
        }else if(node.highlight){
            gctx.strokeStyle = HIGHLIGHT_COLOR;
            gctx.lineWidth = 4;
        }else{
            gctx.strokeStyle = "#000";
            gctx.lineWidth = 1;
        }
        gctx.beginPath();
        gctx.arc(node.x, node.y, node.r, 0, 2 * Math.PI);
        gctx.stroke();
        gctx.strokeStyle = "#000";
        gctx.fillStyle = "#000";

        //add the label
        gctx.font = node.fs + "px Proggy";
        gctx.textAlign = "center";
        gctx.fillText(node.label, node.x, node.y+(node.fs/4));

        //add the index (outside)
        // gctx.font = "20px monospace";
        // gctx.textAlign = "center";
        // gctx.fillText(i, node.x-node.r, node.y-node.r);

        //put the label on the inside
        let idx_fs = parseInt(node.fs/2);
        gctx.font = idx_fs+"px monospace";
        gctx.textAlign = "center";
        gctx.fillText(i, node.x, node.y-idx_fs-2);
    }

    //reset colors just in case
    gctx.strokeStyle = "#000";
    gctx.fillStyle = "#000";
    gctx.lineWidth = 1;
}


// draw each edge in the graph
function drawEdges(){
    //draw the edges
    let ang = [];
    let de = [];
    let et = [];
    for(let i = 0; i < G_EDGES.length; i++){
        let edge = G_EDGES[i];

        //get the line points between the two nodes
        let x1 = edge.n1.x;
        let y1 = edge.n1.y;
        let x2 = edge.n2.x;
        let y2 = edge.n2.y;
        let xm = (x1 + x2) / 2;  //midpoint x
        let ym = (y1 + y2) / 2;  //midpoint y
        let cx = graph_canvas.width/2;
        let cy = graph_canvas.height/2;

        let estr = edge.edge_key;
        let self_edge = (edge.n1 == edge.n2);


        // set the color of the line based on the highlight
        if(edge.select){
            gctx.strokeStyle = SELECT_COLOR;
            gctx.lineWidth = 3;
        }else if(edge.highlight){
            gctx.strokeStyle = HIGHLIGHT_COLOR;
            gctx.lineWidth = 3;
        }else{
            gctx.strokeStyle = "#000000";
            gctx.lineWidth = 1;
        }
        //draw the line
        gctx.beginPath();
        gctx.moveTo(x1,y1);

        // double line
        if(edge.double_edge){
            let inv_pt_d = dist({x:x1,y:y1},{x:xm,y:ym})/2;
            let alt_pts = getPerpBisectors(edge.n1,edge.n2,inv_pt_d);
            let ei = (de.indexOf(oppEdge(estr)) == -1) ? 0 : 1;
            edge.invis_pt = alt_pts[ei];
            edge.invis_pt_d = inv_pt_d;
            gctx.quadraticCurveTo(alt_pts[ei].x, alt_pts[ei].y, x2, y2)   //need to get perpendicular line to pull the quadratic curve to
            et.push("double");
        }

        // straight line
        else if(edge.n1 != edge.n2){
            gctx.lineTo(x2,y2);
            et.push("single");
        }

        // loop
        else if(self_edge){
            // make an arc to loop around
            let r2 = edge.n1.r*(2/3);

            //get the angle from the center of the canvas
            let c_angle = Math.atan2(y1 - cy, x1 - cx);

            edge.invis_pt = {x:(x1+edge.n1.r*(6/5)*Math.cos(c_angle)),y:(y1+edge.n1.r*(6/5)*Math.sin(c_angle)), r:r2};  //point of the 2 circle

            // make the mini loop on the node
            gctx.beginPath();
            gctx.arc((x1+edge.n1.r*(6/5)*Math.cos(c_angle)), (y1+edge.n1.r*(6/5)*Math.sin(c_angle)), r2, 0, 2 * Math.PI);
        }

        gctx.stroke();
        // debugPoint(edge.invis_pt, "blue", 5);


        // add angle 
        // gctx.fillText(edge_angle.toFixed(2) + "|" + estr, (x1+x2)/2, (y1+y2)/2 +(i%2*10));

        // draw the arrow at the midpoint of the edge
        // find midpoint of alt point and midpoint
        let edge_angle = Math.atan2(y1 - y2, x1 - x2);   // has to be recalculated each time for the nodes that get moved
        let angle_point = null;
        if(edge.double_edge)
            angle_point = {x: (edge.invis_pt.x+xm)/2, y: (edge.invis_pt.y+ym)/2};
        else if(self_edge){
            let c_ang = Math.atan2(y1 - cy, x1 - cx);
            angle_point = {x: edge.invis_pt.x+edge.invis_pt.r*Math.cos(c_ang), y: edge.invis_pt.y+edge.invis_pt.r*Math.sin(c_ang)};
        }else
            angle_point = {x: (x1+x2)/2, y: (y1+y2)/2};
        
        // add 2 lines to the angle point
        if(self_edge){
            let tilt = Math.PI/6;
            let c_ang = Math.atan2(y1 - cy, x1 - cx)+Math.PI/2.5;
            gctx.lineWidth = 2*(edge.highlight || edge.select ? 2 : 1);
            gctx.beginPath();
            gctx.moveTo(angle_point.x, angle_point.y);
            let to_pt = {x:angle_point.x-15*Math.cos(c_ang+tilt), y:angle_point.y-15*Math.sin(c_ang+tilt)};
            let to_pt2 = {x:angle_point.x-15*Math.cos(c_ang-tilt), y:angle_point.y-15*Math.sin(c_ang-tilt)};
            gctx.lineTo(to_pt.x, to_pt.y);
            gctx.stroke();
            gctx.beginPath();
            gctx.moveTo(angle_point.x, angle_point.y);
            gctx.lineTo(to_pt2.x, to_pt2.y);
            gctx.stroke();
            gctx.lineWidth = 1;
        }
        
        // double and single lines
        else{
            gctx.lineWidth = 2*(edge.highlight || edge.select ? 2 : 1);
            gctx.beginPath();
            gctx.moveTo(angle_point.x, angle_point.y);
            gctx.lineTo(angle_point.x-15*Math.cos(edge_angle+Math.PI/6), angle_point.y-15*Math.sin(edge_angle+Math.PI/6));
            gctx.stroke();
            gctx.beginPath();
            gctx.moveTo(angle_point.x, angle_point.y);
            gctx.lineTo(angle_point.x-15*Math.cos(edge_angle-Math.PI/6), angle_point.y-15*Math.sin(edge_angle-Math.PI/6));
            gctx.stroke();
            gctx.lineWidth = 1;
        }

        // set the bounding box
        edge.make_bound_box(10,edge.double_edge);
        // debugPoly(edge.bbox, "red")


        // add the edge label (rotated)
        let edge_fs = parseInt(edge.n1.fs*0.75);
        gctx.font = edge_fs+"px monospace";
        gctx.textAlign = "center";
        gctx.save();

        //normal edge
        if(!self_edge){
            gctx.translate(angle_point.x, angle_point.y);
            gctx.rotate(Math.abs(edge_angle) > 2 ? edge_angle + Math.PI : edge_angle)
            gctx.fillText(edge.label, 0, -edge.label_dist);
        }
        //self loop
        else{
            let e_len = 25;
            let ext = Math.atan2(angle_point.y - edge.invis_pt.y, angle_point.x - edge.invis_pt.x);
            let ext_pt = {x:angle_point.x+e_len*Math.cos(ext), y:angle_point.y+e_len*Math.sin(ext)}
            gctx.translate(ext_pt.x, ext_pt.y);
            gctx.rotate(Math.abs(edge_angle) > 2 ? edge_angle + Math.PI : edge_angle)
            gctx.fillText(edge.label, 0, 4);
        }

        gctx.restore();

        de.push(estr);   //keep track of which edges have been drawn (for use with the bends)
  
    }

    // DEBUG(JSON.stringify(G_EDGES[0].bbox))
}


// render the graph canvas
function renderGraph(){
    // clear the canvas
    gctx.clearRect(0, 0, graph_canvas.width, graph_canvas.height);

    //draw the graph
    drawEdges();
    drawNodes();

}



/////////////////////////////    INTERACTION FUNCTIONS    /////////////////////////////


// from https://stackoverflow.com/questions/28284754/dragging-shapes-using-mouse-after-creating-them-with-html5-canvas

// listen for mouse events on the canvas
graph_canvas.onmousedown = mouseDown;
graph_canvas.onmouseup = mouseUp;
graph_canvas.onmouseleave = offScreen;
graph_canvas.onmousemove = mouseMove;

var active_dbl_click = false;

// check if the mouse was double clicked
function dblclick(){
    if(!active_dbl_click){
        active_dbl_click = true;
        setTimeout(function(){active_dbl_click = false;}, 500);
        return false;
    }else{
        return true;
    }
}

// get the position of the mouse relative to the bounding box of the canvas
function getMousePos(e, int_form=true){
    let mp = {
        // x: e.clientX - graph_bound.left,
        // y: e.clientY - graph_bound.top
        x: (e.offsetX * graph_canvas.width) / graph_canvas.clientWidth,
        y: (e.offsetY * graph_canvas.height) / graph_canvas.clientHeight
    };

    if(int_form){
        mp.x = parseInt(mp.x);
        mp.y = parseInt(mp.y);
    }
    return mp;
}

// return whether the x,y position is inside the node
// based on pythagorean theorem
function posInNode(x,y,node){
    return node.r**2 >= (x-node.x)**2 + (y-node.y)**2;
}

// return whether the x,y position is inside the bounding box of the edge
function posInEdge(x,y,edge){
    // make the 4 line segments from the bbox
    let bbox = edge.bbox;
    let segs = [];
    for(let i=0;i<3;i++){
        segs.push([bbox[i], bbox[i+1]]);
    }
    segs.push([bbox[3], bbox[0]]);

    // create line segment for the mouse position
    let mouse_seg = [{x:x,y:y}, {x:graph_canvas.width,y:y}];
    // debugPoly([mouse_seg,mouse_seg], "green")

    // check if the mouse segment intersects any of the bbox segments
    let inter_ct = 0;
    for(let i=0;i<segs.length;i++){
        if(crosses(segs[i], mouse_seg))
            inter_ct++;
    }

    if (inter_ct % 2 == 0)
        return false;
    else
        return true;
}


// handle mouse down/click events on the canvas
function mouseDown(e){
    // tell the browser we're handling this mouse event
    e.preventDefault();
    e.stopPropagation();

    
    // find the node being dragged
    let m = getMousePos(e);
    cur_drag_node = null;

    // check if the mouse is in a node
    let in_node = null;
    for(let i = 0; i < G_NODES.length; i++){
        let node = G_NODES[i];
        if(posInNode(m.x, m.y, node)){
            in_node = node;
            if(dblclick()){             // modify the node on double click
                
            }else{                      // select the node on a single click
                unselectAll();
                selectNode(i);
                cur_drag_node = node;   // allow to be dragged as well
            }
            break;
        }
    }

    // check if mouse is in an edge
    let in_edge = null;
    for(let i = 0; i < G_EDGES.length; i++){
        let edge = G_EDGES[i];
        if(posInEdge(m.x, m.y, edge)){
            in_edge = edge;
            if(dblclick()){             // modify the edge on double click
                
            }else{                      // select the edge on a single click
                unselectAll();
                selectEdge(edge.edge_key);
            }
            break;
        }
    }

    // unselect
    if(in_edge == null && in_node == null){
        unselectAll();
        cur_selection = null;
    }

    //save the current mouse position
    mouse_pos = m;

    //redraw the graph
    renderGraph();

    //activate a double click for any check
    if(!active_dbl_click)
        dblclick();
}

// handle mouse up events on the canvas
function mouseUp(e){
    // tell the browser we're handling this mouse event
    e.preventDefault();
    e.stopPropagation();

    // clear the current drag node
    if(cur_drag_node)
        cur_drag_node.drag = false;
    cur_drag_node = null;

    //unselect everything
    // unselectAll();

    renderGraph();
}

// handle mouse move events on the canvas
function mouseMove(e){
    // tell the browser we're handling this mouse event
    e.preventDefault();
    e.stopPropagation();

    // if we're dragging a node, update its position
    if(cur_drag_node){
        let m = getMousePos(e);

        //moving?
        if(cur_drag_node.drag || m.x != mouse_pos.x || m.y != mouse_pos.y){
            cur_drag_node.drag = true;
        }else{
            cur_drag_node.drag = false;
        }

        cur_drag_node.x += m.x - mouse_pos.x;
        cur_drag_node.y += m.y - mouse_pos.y;
        mouse_pos = m;
        
        renderGraph();
    }

    // if we're hovering over a node, highlight it
    else{
        let m = getMousePos(e);
        let hover_node = null;
        for(let i = 0; i < G_NODES.length; i++){
            let node = G_NODES[i];
            if(posInNode(m.x, m.y, node)){
                hoverNode(i);
            }else{
                unhoverNode(i);
            }
        }

        // if we're hovering over an edge, highlight it
        for(let i = 0; i < G_EDGES.length; i++){
            let edge = G_EDGES[i];
            if(posInEdge(m.x, m.y, edge)){
                hoverEdge(edge.edge_key);
            }else{
                unhoverEdge(edge.edge_key);
            }
        }

        renderGraph();
    }

    //laser pointer
    // let m = getMousePos(e);
    // let mouse_seg = [{x:m.x,y:m.y}, {x:graph_canvas.width,y:m.y}];
    // debugPoly(mouse_seg, "green")
}

// when the mouse leaves the canvas
function offScreen(){
    mouseUp();
    unhoverAll();
}


// highlight a specific node
function hoverNode(ni){
    if(G_NODES[ni].select || (cur_drag_node && cur_drag_node.idx == G_NODES[ni])) return;

    G_NODES[ni].highlight = true;   //highlight the graph node
    document.getElementById("node_"+ni).classList.add("node-item-hover"); //highlight the node in the list
}
// unhighlight a specific node
function unhoverNode(ni){
    G_NODES[ni].highlight = false;
    document.getElementById("node_"+ni).classList.remove("node-item-hover");
}

// highlight a specific edge
function hoverEdge(pair){
    // retrieve index of pair
    let ei = G_EDGES.findIndex(e => e.edge_key == pair);

    if(G_EDGES[ei].select) return;
    G_EDGES[ei].highlight = true;
    document.getElementById("edge_"+pair).classList.add("edge-item-hover");

    // hover over 
}
// unhighlight a specific edge
function unhoverEdge(pair){
    // retrieve index of pair
    let ei = G_EDGES.findIndex(e => e.edge_key == pair);

    G_EDGES[ei].highlight = false;
    document.getElementById("edge_"+pair).classList.remove("edge-item-hover");
}

// unhighlight all nodes and edges
function unhoverAll(){
    for(let i = 0; i < G_NODES.length; i++)
        G_NODES[i].highlight = false;
    
    for(let i = 0; i < G_EDGES.length; i++)
        G_EDGES[i].highlight = false;
}

// select a specific node
function selectNode(ni){
    // unselect everything else
    unselectAll();


    let node = G_NODES[ni];
    G_NODES[ni].select = true;
    G_NODES[ni].highlight = false;
    cur_selection = node;
        
    // DEBUG("selecting node "+ni)
    
    // highlight the node in the list
    document.getElementById("node_"+ni).classList.add("node-item-select");
    document.getElementById("node_"+ni).classList.remove("node-item-hover");

}

// unselect a specific node
function unselectNode(ni){
    G_NODES[ni].select = false;

    // unhighlight the node in the list
    document.getElementById("node_"+ni).classList.remove("node-item-select");
}

// select a specific edge
function selectEdge(pair){
    // unselect everything else
    unselectAll();

    // retrieve index of pair
    let ei = G_EDGES.findIndex(e => e.edge_key == pair);

    G_EDGES[ei].select = true;
    G_EDGES[ei].highlight = false;
    cur_selection = G_EDGES[ei];

    // DEBUG("selecting edge "+pair)

    // highlight the edge in the list
    document.getElementById("edge_"+pair).classList.add("edge-item-select");
    document.getElementById("edge_"+pair).classList.remove("edge-item-hover");
}

// unselect a specific edge
function unselectEdge(pair){
    // retrieve index of pair
    let ei = G_EDGES.findIndex(e => e.edge_key == pair);

    G_EDGES[ei].select = false;

    // unhighlight the edge in the list
    document.getElementById("edge_"+pair).classList.remove("edge-item-select");
}

// unselect all nodes and edges
function unselectAll(){
    for(let i = 0; i < G_NODES.length; i++){
        G_NODES[i].select = false;
        document.getElementById("node_"+i).classList.remove("node-item-select");
    }
    
    for(let i = 0; i < G_EDGES.length; i++){
        G_EDGES[i].select = false;
        document.getElementById("edge_"+G_EDGES[i].edge_key).classList.remove("edge-item-select");
    }

    cur_selection = null;
}