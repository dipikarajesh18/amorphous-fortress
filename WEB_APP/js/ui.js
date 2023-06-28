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