function setTrustScore(msin, displayId) {
    trustScore = getTrustScore(msin);
    $('#' + displayId).html(trustScore);
}

function getTrustScore(msin) {
    result = 'Trust score could not be calculated';
    $.ajax({
        method: "GET",
        url: "/trust_score/" + msin,
        contentType: "application/json",
        async: false,
        success: function(data) {
            data = JSON.parse(data);
            result = 'No trust links between you and the user were found. A trust score could not be calculated.'
            if (data['links'] != 0) {
                result = 'Trust score: ' + data['score'] + ', Trust links: ' + data['links'];
            }
        }
    })
    return result;
}