function hide(contentType, contentIdentifier, contentDescription, buttonId) {
    // Hide the row containing the data that's supposed to be hidden
    $('#' + buttonId).closest('tr').hide()
    // Save hiding preferences to local database
    $.ajax({
        method: "POST",
        url: "/hide",
        contentType: "application/json",
        data: JSON.stringify({
            'contentType': contentType,
            'contentIdentifier': contentIdentifier,
            'contentDescription': contentDescription
        })
    })
}

function unhide(contentType, contentIdentifier, buttonId) {
    // Hide the row containing the data that's supposed to be hidden
    $('#' + buttonId).closest('tr').hide()
    // Save hiding preferences to local database
    $.ajax({
        method: "POST",
        url: "/unhide",
        contentType: "application/json",
        data: JSON.stringify({
            'contentType': contentType,
            'contentIdentifier': contentIdentifier
        })
    })
}