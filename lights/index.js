
let pubnub;
let interval = 25;
let mode; 
let rgbObj;

let intervalChange = (val) => {
  interval = val;
  let label = document.getElementById("updateLabel");
  let value = "";
  if (val < 60){
    value = `${val} Seconds`;
  }else {
      value = `${new Date(val * 1000).toISOString().substr(15, 4)} Minutes`;
  }
  label.innerText = `Update Interval: ${value}`
  console.log(val);
}


let main = () => {

  // Create a new color picker instance
  // https://iro.js.org/guide.html#getting-started
  var colorPicker = new iro.ColorPicker("#picker", {
    // color picker options
    // Option guide: https://iro.js.org/guide.html#color-picker-options
    width: 280,
    color: "rgb(255, 0, 0)",
    // borderWidth: 1,
    // borderColor: "#fff",
  });

  var r = document.getElementById("r");
  var g = document.getElementById("g");
  var b = document.getElementById("b");

  colorPicker.on(["color:init", "color:change"], function (color) {
    rgbObj = color.rgb;
    r.value = color.rgb.r;
    g.value = color.rgb.g;
    b.value = color.rgb.b;
  });

  hexInput.addEventListener('change', function () {
    colorPicker.color.hexString = this.value;
  });
}


const setupPubNub = () => {
  // Update this block with your publish/subscribe keys
  pubnub = new PubNub({
      publishKey : "pub-c-ddb4763f-caaa-47ed-a300-38cfe86853c7",
      subscribeKey : "sub-c-a10298f5-e42a-423e-825b-559ee20ee71b",
      userId: "951a1779-30bb-45d3-9d45-a07faa0ca347",
      uuid: "951a1779-30bb-45d3-9d45-a07faa0ca347"
  });

};

// paste below "publish message" comment
const publishMessage = async () => {


  const form = document.querySelector('form');
  let values = Object.values(form).reduce((obj,field) => { obj[field.id] = field.checked; return obj }, {});
  // Object { solid: true, chase: false, boom: false, pulse: false, undefined: undefined }
  console.log(values)

  let mode = 0;
  mode = values.solid ? 0 : mode;
  mode = values.chase ? 1 : mode;
  mode = values.boom ? 2 : mode;
  mode = values.pulse ? 3 : mode;


  // With the right payload, you can publish a message, add a reaction to a message,
  // send a push notification, or send a small payload called a signal.
  const publishPayload = {
      channel : "mxchip",
      message: {
        colour: rgbObj, 
        mode: mode, 
        interval: interval
      }
  };
  await pubnub.publish(publishPayload);
}





document.addEventListener("DOMContentLoaded", () => {
  setupPubNub();
  main();
});