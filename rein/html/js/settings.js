function postError(data) {
    if (data != 'true') {
        alert('Your desired setting could not be saved.')
    } else {
        alert('Setting saved successfully!')
    }
}

function setFee() {
    fee = $('#feeInput').val();
    $.ajax({
        method: "POST",
        url: "/config",
        contentType: "application/json",
        data: JSON.stringify({
            'key': 'fee',
            'value': fee
        }),
        success: function(data) {
            postError(data);
        }
    })
}

function setTrustScore() {
    trustScoreEnabled = $('#trustScore').is(':checked');
    $.ajax({
        method: "POST",
        url: "/config",
        contentType: "application/json",
        data: JSON.stringify({
            'key': 'trust_score',
            'value': trustScoreEnabled.toString()
        }),
        success: function(data) {
            postError(data);
        }
    })
}