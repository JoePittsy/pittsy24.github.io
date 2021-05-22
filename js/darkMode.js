function toggleNightMode(){
	if (localStorage.night == "true"){
		localStorage.night = "false";

		nightModeOff();
	}else{
		localStorage.night = "true";

		nightModeOn();
	}
}
function nightModeOn(){
	document.documentElement.setAttribute('data-theme', 'dark');
}

function nightModeOff(){
	document.documentElement.setAttribute('data-theme', 'light');
}



if (localStorage.night == "true"){
	nightModeOn();
}else{nightModeOff();}


window.addEventListener('load', function () {	// Create the measurement node
	var scrollDiv = document.createElement("div");
	scrollDiv.className = "scrollbar-measure";
	document.body.appendChild(scrollDiv);

	// Get the scrollbar width
	var scrollbarWidth = scrollDiv.offsetWidth - scrollDiv.clientWidth;

	// Delete the DIV 
	document.body.removeChild(scrollDiv);


	var root = document.compatMode == 'BackCompat' ? document.body : document.documentElement;
	var isVerticalScrollbar = root.scrollHeight > root.clientHeight;

	if (isVerticalScrollbar){
		console.log("SCROLL PADDING BY" + scrollbarWidth)
		document.getElementsByTagName("body")[0].style.padding = "0 0px 8rem " + scrollbarWidth + "px"
	}
	else{
		document.getElementsByTagName("body")[0].style.padding = "0 " + scrollbarWidth + "px 8rem " + scrollbarWidth + "px"

	}
	var bb = document.getElementById("blogBox");
	if (bb) bb.style.height = "unset"


})