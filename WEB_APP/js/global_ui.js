/*
 * GLOBAL_UI.JS
 * Code for the global functions and variables used within the web app
 * Written by: Milk + Github Copilot
*/


///////////////////////////////     GLOBAL VARIABLE DECLARATIONS     ///////////////////////////////


/// graph definitions ///
var CUR_CHAR = "";     // the current character's ASCII
var CUR_NAME = "";     // the current character's name
var CUR_NODES = [];    // order in the array corresponds to node index
var CUR_EDGES = {};    // key is the node-to-node pairing (e.g. "0-1" for node 0 to node 1) and value is the edge label

// (based on beta_config.yaml definitions)
var NODE_SET = ['idle', 'take', 'move', 'die', 'chase', 'clone','add','transform','push']
var EDGE_SET = ['none','touch ?', 'step #', 'within ? #', 'nextTo ?']

/// canvas definitions ///
var graph_div = document.getElementById("gfx-editor");
var graph_canvas = document.getElementById("graph-canvas");
graph_canvas.width = 615;
graph_canvas.height = 625;
var gctx = graph_canvas.getContext("2d");

/// node color changes ///
var HIGHLIGHT_COLOR = "#00B6FF";  
var SELECT_COLOR = "#00EC16";
var DRAG_COLOR = "#FFD200";

/// mouse definitions ///
var graph_bound = graph_canvas.getBoundingClientRect();
var cur_drag_node  = null;
var cur_selection = null;   // can be a node or an edge
var mouse_pos = {x:0, y:0};

/// keypress definitions ///
var DELETE_KEY = "x";
var ADD_KEY = "c";


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


