// Initialize data table and order by ELO
httpGetAsync("https://pong-ratings.herokuapp.com/get_teams_history", theCallback);

function theCallback(responseText) {
    var responseData = JSON.parse(responseText);

    var game_history = [];

    for (var teamKey in responseData) {
        var team = responseData[teamKey]
        var team_item = [];
        team_item.push(team["player"]);
        team_item.push(team["ELO"].toFixed(0));
        team_item.push(team["wins"]);
        team_item.push(team["losses"]);
        team_item.push(team["win_pct"].toFixed(2) + " %");
        team_item.push(team["current_win_streak"]);
        team_item.push(team["longest_win_streak"]);

        game_history.push(team_item);
    }

    $('#teams').DataTable( {
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