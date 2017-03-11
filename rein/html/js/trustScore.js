function setTrustScore(msin, displayId) {
    trustScore = getTrustScore(msin);
    $('#' + displayId).html(trustScore);
}

function getTrustScore(msin) {
    return msin;
}