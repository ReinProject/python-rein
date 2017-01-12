function getJobs() {
	// Fetches the ten most recent jobs the user was involved in
	$.getJSON($SCRIPT_ROOT + '/get-jobs', {
		user: 'test_hash'
	}, function(data) {
		return data.result;
	});
	return true;
}

function getUsers() {
	// Fetches all users involved in a job: [employer, mediator, employee]
	return
}