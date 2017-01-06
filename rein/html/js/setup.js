function storeUserData() {
    var errors = '';
    // Check if name and contact are valid.
    var name = document.getElementById('name').value;
    var contact = document.getElementById('contact').value;
    if (name.length > 0 && contact.length > 0) {
        sessionStorage.name = name;
        sessionStorage.contact = contact;
    } else {
        errors += "Name or contact are invalid.\n\n";
    }
    // Choose the 'mediate' value.
    var radios = document.getElementsByName('mediator');
    for (var i = 0, length = radios.length; i < length; i++) {
    if (radios[i].checked) {
        var mediate = sessionStorage.mediate = radios[i].value;
        break;
        }
    }
    // Check mediator fee.
    var mediatorFee = document.getElementById('fee').value;
    if (mediate === "True") {
        if (isNaN(parseInt(mediatorFee))) {
            errors += "Invalid fee, should be number.\n\n";
        } else {
            sessionStorage.mediatorFee = mediatorFee;
        }
    } else {
        sessionStorage.mediatorFee = 0;
    }
    // Display errors if any.
    if (errors != '') {
        document.getElementById("errors").innerText = errors;
        return false;
    } else {
        return true;
    }
}
// -------------------------
function getMnemonic() {
    var mnemonics = { "english": new Mnemonic("english") }["english"];
    var mnemonic = mnemonics.generate();
    document.getElementById('ajax-header').innerText = "Generating access keys"
    document.getElementById('ajax-description').innerHTML = "<span style='font-size: 12pt'>Put down on paper these 12 words. They are the key to accessing and recovering your Rein account.</span><br>"
    document.getElementById('ajax-elements').innerHTML = "<br><p style='font-size: 13pt'>" + mnemonic + "</p>";
    document.getElementById('ajax-button').removeAttribute('class')
    document.getElementById('ajax-button').setAttribute('class', 'col-sm-6')
    document.getElementById('ajax-button').innerHTML = "<br><button onclick='renderConfirmMnemonic()'>Next</button>"
    sessionStorage.mnemonic = mnemonic;
    sessionStorage.seed = mnemonics.toSeed(mnemonic);
}
// -------------------------
function renderConfirmMnemonic() {
    document.getElementById('ajax-header').innerText = "Confirm that you wrote down the mnemonic";
    document.getElementById('ajax-description').innerText = '';
    var wordsToCheck = [1, 2, 3, 10, 11, 12];
    sessionStorage.wordsToCheck = wordsToCheck;
    var ajaxHtml = '<div class="row"><div class="col-xs-12 col-sm-12"><form class="form-horizontal">';
    for (var i = 0, len = wordsToCheck.length; i < len; i++) {
        wordNo = wordsToCheck[i]
        ajaxHtml += '<div class="form-group"><label class="col-sm-3 control-label">Word ' + 
                    wordNo + ':</label><div class="col-sm-6"><input type="text" id="word' + 
                    wordNo + '" title="Word ' + wordNo + '"></div></div>';
    }
    ajaxHtml += '</form></div></div>';
    document.getElementById('ajax-elements').innerHTML = ajaxHtml;
    document.getElementById('ajax-button').removeAttribute('class')
    document.getElementById('ajax-button').setAttribute('class', 'col-sm-offset-3 col-sm-6')
    document.getElementById('ajax-button').innerHTML = "<button onclick='confirmMnemonic()'>Next</button>"
}
// -------------------------
function confirmMnemonic() {
    // TODO - Add a retry counter
    mnemonic = sessionStorage.mnemonic.split(' ');
    wordsToCheck = sessionStorage.wordsToCheck;
    conditions = [];
    for (var i = 0, len = wordsToCheck; i < len; i++) {
        wordNo = wordsToCheck[i];
        conditions[i] = document.getElementById('word' + wordNo).value == mnemonic[wordNo - 1];
    }
    for (var i = 0; i < conditions.length; i++) {
        if (conditions[i] == false) {
            errors = "Some of the words you entered is incorrect. Try again.\n";
            document.getElementById('errors').innerText = errors;
            return
        }
    }
    submitData();
}
// -------------------------
function submitData() {
    urlEncodedDataPairs = ['name=' + sessionStorage.name, 'contact=' + sessionStorage.contact, 
                           'mediate=' + sessionStorage.mediate, 'mediatorFee=' + sessionStorage.mediatorFee, 
                           'seed=' + sessionStorage.seed];
    urlEncodedData = urlEncodedDataPairs.join('&').replace(/%20/g, '+');
    var xhttp = new XMLHttpRequest();
    xhttp.open('POST', 'http://127.0.0.1:5001/register-user', true);
    xhttp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhttp.send(urlEncodedData);
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var response = JSON.parse(this.responseText);
            if (response.enrolled) {
                window.location.replace('http://127.0.0.1:5001/done');
            } else {
                alert('Try restarting "rein start" or submit the form again.')
            }
        }
    };
}