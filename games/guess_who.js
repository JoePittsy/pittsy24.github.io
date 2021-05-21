window.onload = function () {
    var names = $("area").toArray().map(e => e.title)
    const player_name = names[Math.floor(Math.random() * names.length)];
    $("#player")[0].innerHTML = `You Are: ${player_name}`
};


$("area").click( e => {
    coords = e.currentTarget.coords.split(',')

    var cover = $('<div class = "guess-who-cover", onclick="$(this).remove()"></div>');
    var a = Math.random() * 10 - 5;
    cover.css('transform', 'rotate(' + a + 'deg) scale(.9)')

    
    $('#guess').append(cover);   
    var offset = ($("#guess").width() - $("#guess img").width()) / 2
    console.log(offset)
    cover.css({ 'top': Number(coords[1]) - 5 + 'px', 'left': Number(coords[0]) + offset +'px'})


})