// Initialize data table and order by Date
httpGetAsync("http://pong-ratings.herokuapp.com/get_game_history", theCallback);

function theCallback(responseText) {
    var responseData = JSON.parse(responseText);

    var game_history = [];

    for (var gameKey in responseData) {
        var game = responseData[gameKey]
        var game_item = [];
        game_item.push(game["entryDate"]);
        game_item.push(game["score"]);
        game_item.push(game["wt"]);
        game_item.push(game["lt"]);
        game_history.push(game_item);
    }
    
    $('#games').DataTable( {
            "paging": false,
            "order": [[ 0, 'desc' ]],
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