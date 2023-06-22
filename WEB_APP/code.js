// edit the character and entity name
var char_in = document.getElementById("char_in");
var char_txt = document.getElementById("char_txt");
var name_in = document.getElementById("name_in");
var name_txt = document.getElementById("name_txt");


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

// 
char_txt.addEventListener("dblclick", function(){showTxtIn(char_txt,char_in)});
char_in.addEventListener("blur", function(){hideTxtIn(char_txt,char_in)});
char_in.addEventListener("keyup", function(e){if(e.key == "Enter"){hideTxtIn(char_txt,char_in)}})

name_txt.addEventListener("dblclick", function(){showTxtIn(name_txt,name_in)});
name_in.addEventListener("blur", function(){hideTxtIn(name_txt,name_in)});
name_in.addEventListener("keyup", function(e){if(e.key == "Enter"){hideTxtIn(name_txt,name_in)}})

