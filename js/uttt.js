var url = new URL("http://joepitts.co.uk/games/ttt.html");
var player;
var peer;
var peerID;
var conn;
let passcode = [];


var opponentsName = "Player ";

var grid;

var running = true;
var myGo;
var fullGrids = [];
// grid[1][1].children().children(small[0][1]);

var small = [
  [".top.left", ".top.middle", ".top.right"],
  [".mid.left", ".mid.middle", ".mid.right"],
  [".bot.left", ".bot.middle", ".bot.right"],
];

function nameChange() {
  var t = $(`#ttt_player${player} input`)[0];
  t.style.width = t.value.length + 1 + "ch";

  let n = { name: "" };
  n.name = t.value;

  conn.send(JSON.stringify(n));
}

function changeOtherPlayersName(data) {
  opponentsName = data;
  var input = $(`#ttt_player${player} input`)[0].outerHTML;
  var v = $(`#ttt_player${player} input`)[0].value;

  if (player === 2) {
    $(`#ttt_player${player}`)[0].innerHTML = `${data} Vs ${input}`;
  } else {
    $(`#ttt_player${player}`)[0].innerHTML = `${input} Vs ${data}`;
  }
  $(`#ttt_player${player} input`)[0].value = v;
}



// We're connecting to them
function connect(id) {
  conn = peer.connect(id);
  conn.on("open", () => {
    console.log("Connection established");
    player = 2;
    showGame();
    conn.on("data", messageHandler);
  });
}

function messageHandler(data) {
  if (!running) {
    disablePointer();
    return;
  }
  console.log(data);

  let obj = JSON.parse(data);
  if (obj.name !== undefined) {
    changeOtherPlayersName(obj.name);
  }
  else{
    $("#ttt_playersturn").text("It's my turn");
  // We got a coord

  // grid[1][1].children().children(small[0][1]);
  grid[obj.clicked[1]][obj.clicked[0]]
    .children()
    .children(small[obj.square[1]][obj.square[0]])
    .addClass(player == 1 ? "p2" : "p1")
    .css("pointer-events", "none");

  checkWin(
    $($(grid[obj.clicked[1]][obj.clicked[0]].children())),
    obj.square[0],
    obj.square[1],
    player == 1 ? 2 : 1
  );

  disablePointer();
  if(running){
    enablePointer([[obj.square[1], obj.square[0]]]);

  }
  }


}

function squareToIndex(square) {
  let replacerX = { left: 0, middle: 1, right: 2 };
  let replacerY = { top: 0, mid: 1, bot: 2 };

  let by = replacerY[square[0].parentElement.classList[1]];
  let bx = replacerX[square[0].parentElement.classList[2]];
  return [bx, by];
}

function checkOverallWin(square, plyr) {
  var coords = squareToIndex(square);
  console.log(coords);
  for (var i = 0; i < 3; i++) {
    if (!fullGrids.includes(grid[i][coords[0]])) break;
    if (!grid[i][coords[0]].children().hasClass("p" + plyr)) break;
    if (i == 2) {
      console.log("WIN");
      disablePointer();

      alert(`Player ${plyr} has won!`);
      running = false;
      //report win for s
    }
  }

  for (var i = 0; i < 3; i++) {

    if (!fullGrids.includes(grid[coords[1]][i])) break;
    if (!grid[coords[1]][i].children().hasClass("p" + plyr)) break;
    if (i == 2) {
      console.log("WIN");
      disablePointer();


      alert(`Player ${plyr} has won!`);
      running = false;

      //report win for s
    }
  }

  if (coords[0] == coords[1]) {
    //we're on a diagonal
    for (var i = 0; i < 3; i++) {
      if (!grid[i][i].children().hasClass("p" + plyr)) break;
      if (i == 2) {
        console.log("WIN");
        disablePointer();


        alert(`Player ${plyr} has won!`);
        running = false;
      }
    }
  }

  //check anti diag (thanks rampion)
  if (coords[0] + coords[1] == 2) {
    for (var i = 0; i < 3; i++) {
      if (!grid[i][2 - i].children().hasClass("p" + plyr)) break;
      if (i == 2) {
        console.log("WIN");
        disablePointer();


        alert(`Player ${plyr} has won!`);
        running = false;
      }
    }
  }
}

function checkWin(square, x, y, plyr) {
  console.log(`Checking if player ${plyr} has won by playing at ${x}, ${y}`);
  //Horizontal

  for (var i = 0; i < 3; i++) {
    if (!square.children(small[i][x]).hasClass("p" + plyr)) break;
    if (i == 2) {
      square.addClass("p" + plyr);
      var coords = squareToIndex(square);

      fullGrids.push(grid[coords[1]][coords[0]]);
      console.log("Win");
      checkOverallWin(square, plyr);
    }
  }

  for (var i = 0; i < 3; i++) {
    if (!square.children(small[y][i]).hasClass("p" + plyr)) break;
    if (i == 2) {
      square.addClass("p" + plyr);
      var coords = squareToIndex(square);

      fullGrids.push(grid[coords[1]][coords[0]]);

      console.log("Win");
      checkOverallWin(square, plyr);
    }
  }

  if (x == y) {
    //we're on a diagonal
    for (var i = 0; i < 3; i++) {
      if (!square.children(small[i][i]).hasClass("p" + plyr)) break;
      if (i == 2) {
        square.addClass("p" + plyr);
        var coords = squareToIndex(square);

        fullGrids.push(grid[coords[1]][coords[0]]);

        console.log("Win");
        checkOverallWin(square, plyr);
      }
    }
  }

  //check anti diag (thanks rampion)
  if (x + y == 2) {
    for (var i = 0; i < 3; i++) {
      if (!square.children(small[i][2 - i]).hasClass("p" + plyr)) break;
      if (i == 2) {
        square.addClass("p" + plyr);
        var coords = squareToIndex(square);

        fullGrids.push(grid[coords[1]][coords[0]]);

        console.log("Win");
        checkOverallWin(square, plyr);
        //report win for s
      }
    }
  }
}

function replaceAll(string, selector, value) {
  let rString = string;
  let pString;
  do {
    pString = rString;
    rString = rString.replace(selector, value);
  } while (pString != rString);
  return rString;
}

function resizeGrid() {
  $("#ttt_grid").css("height", $("#ttt_grid").width());
}

function disablePointer() {
  for (let y = 0; y <= 2; y++) {
    for (let x = 0; x <= 2; x++) {
      grid[x][y].css("pointer-events", "none");
      grid[x][y].children().removeClass("ttt_indicate");
    }
  }
}

function squareClicked(elm) {
  $("#ttt_playersturn").text(`It's ${opponentsName}'s turn`);
  console.log(elm);
  $(elm).addClass("p" + player);
  disablePointer();
  myGo = false;

  let replacerX = { left: 0, middle: 1, right: 2 };
  let replacerY = { top: 0, mid: 1, bot: 2 };

  let by = replacerY[elm.parentElement.parentElement.classList[1]];
  let bx = replacerX[elm.parentElement.parentElement.classList[2]];

  let y = replacerY[elm.classList[1]];
  let x = replacerX[elm.classList[2]];

  checkWin($(elm.parentElement), x, y, player);

  let data = {
    clicked: [bx, by],
    square: [x, y],
  };

  console.log({data})
  conn.send(JSON.stringify(data));
  setTimeout(() => {
    if(running){indicate(grid[y][x].children());}
  }, 250)
}

function enablePointer(grids) {
  if (grids === "all") {
    grid.forEach((element) => {
      element.forEach((sub) => {
        if (!fullGrids.includes(sub)) {
          indicate(sub.children());
          sub.css("pointer-events", "all");
        }
      });
    });
  } else {
    for (let i = 0; i < grids.length; i++) {
      if (fullGrids.includes(grid[grids[i][0]][grids[i][1]])) {
        // Aight all available grids
        enablePointer("all");
        return;
      }
      grid[grids[i][0]][grids[i][1]].css("pointer-events", "all");
      let y = grids[i][0];
      let x = grids[i][1];
      indicate(grid[y][x].children());
    }
  }
}

function indicate(elm) {
  //   disablePointer();
  if (elm === "all") {
    grid.forEach((element) => {
      element.forEach((sub) => {
        if (!fullGrids.includes(sub)) {
          indicate(sub.children());
        }
      });
    });
  } else {
    console.log(elm);
    var coords = squareToIndex($(elm));
    if (fullGrids.includes(grid[coords[1]][coords[0]])) {
      indicate("all");
      return;
    }
    $(elm).addClass("ttt_indicate");
    /*  */
  }
}

function showGame() {
  $("#ttt_title").fadeOut();
  $("#ttt_instructions").fadeOut();
  $("#ttt_new_options").fadeOut(
    (callback = () => {
      $("#ttt_gameid").fadeOut();
      $("#ttt_buttons").fadeOut(
        (callback = () => {
          if (player === 1) {
            myGo = true;
            $("#ttt_player1").fadeIn();
          } else {
            myGo = false;
            $("#ttt_player2").fadeIn();
          }
          $("#ttt_playersturn").fadeIn();
          $("#ttt_grid").fadeIn(
            (callback = () => {
              resizeGrid();
              if (myGo) {
                enablePointer("all");
                $("#ttt_playersturn").text("It's my turn");
                opponentsName = "Player Two";
              } else {
                opponentsName = "Player One";
                $("#ttt_playersturn").text(`It's ${opponentsName}'s turn`);
                disablePointer();
                indicate("all");
              }
            })
          );
        })
      );
    })
  );
}

function getWord(callback){
  fetch("https://random-words-api.vercel.app/word")
    .then(data => {
      return data.json();
    }).then(json => {
      callback(json[0].word);
    })
}



$().ready(() => {
  getWord(word => {
    passcode.push(word);
    getWord(word => {
      passcode.push(word);
      getWord(word => {
        passcode.push(word);
        console.log(passcode.join(""))
        peer = new Peer(passcode.join(""));
        grid = [
          [$(".ttt_big.top.left"), $(".ttt_big.top.middle"), $(".ttt_big.top.right")],
          [$(".ttt_big.mid.left"), $(".ttt_big.mid.middle"), $(".ttt_big.mid.right")],
          [$(".ttt_big.bot.left"), $(".ttt_big.bot.middle"), $(".ttt_big.bot.right")],
        ];
        $(".ttt_small").click(function () {
          $(this).off();
          $(this).css("pointer-events", "none");
          squareClicked(this);
        });

        $("#ttt_join").click(() => {
          connect($("#ttt_code")[0].value);
        });

        $("#ttt_create").click(() => {
          $("#ttt_instructions").fadeOut();
          $("#ttt_new_options").fadeOut(
            (callback = () => {
              $("#ttt_gameid")[0].innerHTML =
                'Join Code: <span id = "code">' + peerID + "</span>";
              $("#ttt_copy_url").attr("data-clipboard-text", url.toString());
              $("#ttt_gameid").fadeIn();
              $("#ttt_buttons").fadeIn();

              // $("#ttt_players").fadeIn();
              // $("#ttt_grid").fadeIn(callback=resizeGrid);
            })
          );
        });
        peer.on("open", function (id) {
          console.log("My peer ID is: " + id);
          peerID = id;
          $("#ttt_new_options").fadeIn();
          url.searchParams.append("code", id);

          var u = new URL(window.location);
          var id = u.searchParams.get("code");
          if (id != null) {
            console.log("Attempting connection");
            connect(id);
            // We joining a game bois
          }

          peer.on("connection", function (c) {
            console.log("Connection established");
            player = 1;
            showGame();
            conn = c;
            // They connected to us
            conn.on("open", () => {
              conn.on("data", messageHandler);
            });
          });
        });

      });
    });
  });



});

$(window).on("resize", () => {
  resizeGrid();
});
