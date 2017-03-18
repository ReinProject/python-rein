document.addEventListener("DOMContentLoaded", function(event) {
    $('#userTable').DataTable( {
        "paging":   false,
        "ordering": true,
        "order": [[3, "desc"]],
        "info":     true,
        "searching":   false
    });
});