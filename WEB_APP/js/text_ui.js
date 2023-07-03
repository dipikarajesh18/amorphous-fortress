/*
 * GRAPH_UI.JS
 * Code for the text table UI (right sidebar) and the top menu bar
 * Written by: Milk 
*/

///////////////////////////////     UI DECLARATIONS     ///////////////////////////////

// MENU DROPDOWN
let all_menus = document.getElementsByClassName("menu-item");

// CHARACTER NAME AND ASCII 
var char_in = document.getElementById("char_in");
var char_txt = document.getElementById("char_txt");
var name_in = document.getElementById("name_in");
var name_txt = document.getElementById("name_txt");


/////////////////////////////     FUNCTION DEFINITIONS     /////////////////////////////

// show the input and hide the text
function showTxtIn(txt,ipt){
    txt.style.display = "none";
    ipt.style.display = "block";
    ipt.focus();
}

// hide the input and show the text - save the value
function hideTxtIn(txt,ipt){
    txt.style.display = "block";
    ipt.style.display = "none";
    txt.innerHTML = ipt.value;
}

function showMenu(submenu){
    submenu.style.display = "block";
}
function hideMenu(submenu){
    submenu.style.display = "none";
}


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

///////////////////////////////     EVENT LISTENERS     ///////////////////////////////



// character name and ascii event listeners
char_txt.addEventListener("dblclick", function(){showTxtIn(char_txt,char_in)});
char_in.addEventListener("blur", function(){hideTxtIn(char_txt,char_in)});
char_in.addEventListener("keyup", function(e){if(e.key == "Enter"){hideTxtIn(char_txt,char_in)}})

name_txt.addEventListener("dblclick", function(){showTxtIn(name_txt,name_in)});
name_in.addEventListener("blur", function(){hideTxtIn(name_txt,name_in)});
name_in.addEventListener("keyup", function(e){if(e.key == "Enter"){hideTxtIn(name_txt,name_in)}})

// add event listeners to the menus and submenus            
for(let i = 0; i < all_menus.length; i++){
    let menu = all_menus[i];
    let submenus = menu.children;   //assume only submenus are the only children of the menu items
    if(submenus.length == 0)
        continue;

    menu.addEventListener("click", function(){showMenu(submenus[0])});
    menu.addEventListener("mouseleave", function(){hideMenu(submenus[0])});
    // menu.addEventListener("mouseleave", function(){debug.innerHTML = `mouseout (${submenus[0].id})`;});
}