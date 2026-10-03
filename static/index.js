//========================================================================
// Drag and drop image handling
//========================================================================

var fileDrag = document.getElementById("file-drag");
var fileSelect = document.getElementById("file-upload");

// Add event listeners
fileDrag.addEventListener("dragover", fileDragHover, false);
fileDrag.addEventListener("dragleave", fileDragHover, false);
fileDrag.addEventListener("drop", fileSelectHandler, false);
fileSelect.addEventListener("change", fileSelectHandler, false);

function fileDragHover(e) {
  // prevent default behaviour
  e.preventDefault();
  e.stopPropagation();

  fileDrag.className = e.type === "dragover" ? "upload-box dragover" : "upload-box";
}

function fileSelectHandler(e) {
  // handle file selecting
  var files = e.target.files || e.dataTransfer.files;
  fileDragHover(e);
  for (var i = 0, f; (f = files[i]); i++) {
    previewFile(f);
  }
}

//========================================================================
// Web page elements for functions to use
//========================================================================

var imageDisplay = document.getElementById("image-display");
var uploadCaption = document.getElementById("upload-caption");
var predResult = document.getElementById("pred-result");
var loader = document.getElementById("loader");
var loader1 = document.getElementById("timepass");


//========================================================================
// Main button events
//========================================================================

function submitImage() {
  // action for the submit button
  console.log("submit");

  if (!imageDisplay.src || !imageDisplay.src.startsWith("data")) {
    window.alert("Please select an image before submit.");
    return;
  }

  loader.classList.remove("hidden");
  imageDisplay.classList.add("loading");

  // call the predict function of the backend
  predictImage(imageDisplay.src);
  console.log("im back");
}

function clearImage() {
console.log("in clear")
  // reset selected files
  fileSelect.value = "";

  // remove image sources and hide them
  imageDisplay.src = "";
  predResult.innerHTML = "";
document.getElementById("timepass").innerHTML= "";
  hide(imageDisplay);
  hide(loader);
  hide(predResult);
  show(uploadCaption);

  imageDisplay.classList.remove("loading");
}

function previewFile(file) {
  // show the preview of the image
  console.log(file.name);
  var fileName = encodeURI(file.name);

  var reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onloadend = () => {
    imageDisplay.src = URL.createObjectURL(file);

    show(imageDisplay);
    //hide(uploadCaption);

    // reset
    predResult.innerHTML = "";
    //imageDisplay.classList.remove("loading");

    displayImage(reader.result, "image-display");
  };
}

//========================================================================
// Helper functions
//========================================================================

function predictImage(image) {
  fetch("/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(image)
  })
    .then(resp => {
      resp.json().then(data => {
        displayResult(data);
      }).catch(() => {
        hide(loader);
        document.getElementById("timepass").innerText = "Error: Invalid response from server";
      });
    })
    .catch(err => {
      console.log("An error occured", err.message);
      hide(loader);
      window.alert("Oops! Network error connecting to prediction endpoint.");
    });
}

function displayImage(image, id) {
  // display image on given id <img> element
  let display = document.getElementById(id);
  display.src = image;
  show(display);
}

function displayResult(data) {
  hide(loader);
  const timepassEl = document.getElementById("timepass");
  if (data.status === "success") {
    timepassEl.innerHTML = `<span style="color: #28a745;">${data.result}</span>`;
  } else if (data.status === "unavailable") {
    timepassEl.innerHTML = `<span style="color: #ffc107;">${data.result}</span><br><small style="font-size: 0.9rem; color: #fff;">${data.error}</small><br><span style="font-size: 0.75rem; color: #ccc;">${data.detail || ''}</span>`;
  } else if (data.error) {
    timepassEl.innerHTML = `<span style="color: #dc3545;">${data.error}</span>`;
  } else {
    timepassEl.innerText = data.result || "No result";
  }
}

function hide(el) {
  // hide an element
  el.classList.add("hidden");
}

function show(el) {
  // show an element
  el.classList.remove("hidden");
}