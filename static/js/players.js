// Initialize data table and order by ELO
httpGetAsync("https://pong-ratings.herokuapp.com/get_player_history", theCallback);

function theCallback(responseText) {
    var responseData = JSON.parse(responseText);

    var game_history = [];

    for (var playerKey in responseData) {
        var player = responseData[playerKey]
        var player_item = [];
        player_item.push(player["player"]);
        player_item.push(player["ELO"].toFixed(0));
        player_item.push(player["wins"]);
        player_item.push(player["losses"]);
        player_item.push(player["win_pct"].toFixed(2) + " %");
        player_item.push(player["current_win_streak"]);
        player_item.push(player["longest_win_streak"]);

        game_history.push(player_item);
    }

    $('#players').DataTable( {
            "paging": false,
            "order": [[ 1, 'desc' ]],
            "data": game_history
    } );
}

function httpGetAsync(theUrl, callback) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback(xmlHttp.responseText);
    }

    xmlHttp.open("GET", theUrl, true); // true for asynchronous 
    xmlHttp.send(null);
}