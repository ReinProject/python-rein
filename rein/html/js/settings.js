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
            if (data != 'true') {
                alert('Your desired fee could not be saved.')
            }
        }
    })
}