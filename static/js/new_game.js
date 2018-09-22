// Set Enter keycode to trigger form submit from anywhere on page
function detectEnterKeyStroke(e) {
    // Get window.event
    e = e || window.event;

    // If keyCode == Enter 
    // And Submit Button wasn't focused when enter was pressed
    // (Note: the Submit Button itself triggers it's own modal)
    // And no modal windows are currently open

    if (e.keyCode == 13 && $(e.target).context.name != "submit") {
        if ($('.modal.in').length < 1) {
            submitForm();   
        }
    }
}

function submitForm () {
    var form = document.getElementById("form");
    var winp1 = capitalizeFirstLetter(form.winp1.value);
    var winp2 = capitalizeFirstLetter(form.winp2.value);
    var winScore = parseInt(form.winScore.value);
    var losep1 = capitalizeFirstLetter(form.losep1.value);
    var losep2 = capitalizeFirstLetter(form.losep2.value);
    var loseScore = parseInt(form.loseScore.value);

    var valid = true;
    var double = false;
    var error_message = "\n<ul type=\"circle\">";

    // Check data inputs for validity
    if (winp1 === "") { error_message += "<li>Winning Player 1 is invalid.</li>";  valid = false; }
    
    if (winScore < 0 || isNaN(winScore) || winScore < loseScore || winScore.length < 1 || winScore.length > 2) { error_message += "<li>Winning Score is invalid.</li>";  valid = false; }
    
    if (losep1 === "") { error_message += "<li>Losing Player 1 is invalid.</li>";  valid = false; }

    if (loseScore < 0 || isNaN(loseScore) || loseScore.length < 1 || loseScore.length > 2) { error_message += "<li>Losing Score is invalid.</li>";  valid = false; }
    
    if (winScore === loseScore) { error_message += "<li>There are no ties in ping-pong.</li>";  valid = false; }

    if ((winp2.length === 0 && losep2.length > 0) || (winp2.length > 0 && losep2.length === 0)) { error_message += "<li>Cannot have mismatched team sizes.</li>";  valid = false; }
    
    if ((winp1 === winp2 && winp1.length > 0) || (losep1 === losep2 && losep1.length > 0) || (winp1 === losep1 && winp1.length > 0) || (winp1 === losep2 && winp1.length > 0) || (winp2 === losep1 && winp2.length > 0) || (winp2 === losep2 && winp2.length > 0)) { error_message += "<li>The same player cannot play multiple times.</li>";  valid = false; }
                           
    // Close error message unordered list
    error_message += "</ul>";

    // Generate confirmation message
    var confirm_message = "";

    if (winp2.length > 0 && losep2.length > 0) {
        confirm_message = "Team " + winp1 + " and " + winp2 + " beat Team " + losep1 + " and " + losep2 + " with score " + winScore + " - " + loseScore + "?";
    }
    else {
        confirm_message = winp1 + " beat " + losep1 + " with score " + winScore + " - " + loseScore + "?";
    }

    // Error Dialog
    if (!valid) {
        BootstrapDialog.show({ 
            title:"Invalid Request",
            message:"Not recording game for following reason(s): " + error_message,
            buttons: [{
                label: 'Close',
                hotkey: 13,
                action: function(dialog) {
                    dialog.close();        
                }
            }]
        });
    }
    else { // Confirmation Dialog
        BootstrapDialog.show({
            title: 'Commit New Game',
            message: confirm_message,
            buttons: [{
                label: 'Cancel',
                action: function(dialog) {
                    valid = false;
                    dialog.close();        
                }
            }, {
                label: 'Commit',
                hotkey: 13,
                icon: 'glyphicon glyphicon-check',
                action: function(dialog) {
                    dialog.close();

                    // Submit "commit game" request to our backend
                    var winning_team = winp1;
                    if (winp2.length > 0) {
                        winning_team += " and " + winp2;
                    }

                    var losing_team = losep1;
                    if (losep2.length > 0) {
                        losing_team += " and " + losep2;
                    }

                    var score = winScore + " - " + loseScore;

                    httpGetAsync("https://pong-ratings.herokuapp.com/save_new_game?winning_team=" + winning_team + "&losing_team=" + losing_team + "&score=" + score, theCallback)
                }
            }]
        });
    }
    
    return valid;
}

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1).toLowerCase();
}

function theCallback(responseText) {
    // Success Dialog
    BootstrapDialog.show({
        title: 'Success',
        message: "Successfully committed new game!",
        buttons: [{
            label: 'Close',
            hotkey: 13,
            action: function(dialog) {
                location.reload();
                dialog.close();        
            }
        }]
    });
}

function httpGetAsync(theUrl, callback) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback(xmlHttp.responseText);
    }
    xmlHttp.onloadend = function() {
        if (xmlHttp.status == 404) {
            // Too many recent game commits (ONCE PER 10 seconds)
            BootstrapDialog.show({
                title: 'Too many requests to server in last 10 seconds!',
                message: "Please submit your request again in a few seconds.",
                buttons: [{
                    label: 'Close',
                    hotkey: 13,
                    action: function(dialog) {
                        dialog.close();        
                    }
                }]
            });
        }
    }
    xmlHttp.open("GET", theUrl, true); // true for asynchronous 
    xmlHttp.send(null);
}
