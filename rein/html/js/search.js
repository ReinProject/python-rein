function search(inputId) {
    searchInput = $("#" + inputId).val();
    if (searchInput == "") {
        alert('Please enter user name, msin or contact information of the person you\'re trying to find.')
    }

    $.ajax({
        method: "GET",
        url: "/user_search/" + searchInput,
        contentType: "application/json",
        success: function(data) {
            if (data != 'true') {
                alert('User could not be found')
            }
        }
    })
}