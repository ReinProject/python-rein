function postError(data) {
    if (data != 'true') {
	alert('Error withdrawing.')
    } else {
	alert('Withdrawl succeeded. Please allow some time for it to confirm.')
    }
}

function withdraw_from_job(job_id) {
    var amount = $('#withdraw_amount_'+job_id).val();
    var destaddr = $('#withdraw_address_'+job_id).val();
    $.ajax({
	method: "POST",
	url: "/withdraw",
	contentType: "application/json",
	data: JSON.stringify({
	    'job': job_id,
	    'amount': amount,
	    'addr': destaddr
	}),
	success: function(data) {
	    postError(data);
	}
    })
}
