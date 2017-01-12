function getJobs() {
	// Fetches the ten most recent jobs the user was involved in
	jobs = [];
	$.getJSON($SCRIPT_ROOT + '/get-jobs', {
		user: $USER_ID
	}, function(data) {
		jobs[jobs.length] = data.result;
	});
	return jobs;
}

function setUser() {
	user_id = ''
	user_name = ''
	if ($CURRENT_USER == 0) {
		user_id = $USER_JOBS[$CURRENT_JOB].employer.ID;
		user_name = $USER_JOBS[$CURRENT_JOB].employer.Name;
	} else if ($CURRENT_USER == 1) {
		user_id = $USER_JOBS[$CURRENT_JOB].mediator.ID;
		user_name = $USER_JOBS[$CURRENT_JOB].mediator.Name;
	} else {
		user_id = $USER_JOBS[$CURRENT_JOB].employee.ID;
		user_name = $USER_JOBS[$CURRENT_JOB].employee.Name;
	}
	$("input[name='user_id']").val(user_id);
	$("button.user_name").text(user_name);
	return true;
}

function lastUser() {
	if ($CURRENT_USER == 0) {
		return false;
	}

	$CURRENT_USER = $CURRENT_USER - 1;
	setUser();
	return true;
}


function nextUser() {
	if ($CURRENT_USER == 2) {
		return false;
	}
	$CURRENT_USER = $CURRENT_USER + 1;
	setUser();
	return true;
}

function lastJob() {
	if ($CURRENT_JOB == 0) {
		return false;
	}

	$CURRENT_JOB = $CURRENT_JOB - 1;
	$("input[name='job_id']").val($USER_JOBS[$CURRENT_JOB].job_id);
	$("button.job_name").text($USER_JOBS[$CURRENT_JOB].job_name);
	$CURRENT_USER = 0;
	setUser();
	return true;
}


function nextJob() {
	if ($CURRENT_JOB == $USER_JOBS.length - 1) {
		return false;
	}
	$CURRENT_JOB = $CURRENT_JOB + 1;
	$("input[name='job_id']").val($USER_JOBS[$CURRENT_JOB].job_id);
	$("button.job_name").text($USER_JOBS[$CURRENT_JOB].job_name);
	$CURRENT_USER = 0;
	setUser();
	return true;
}

document.addEventListener("DOMContentLoaded", function(event) {
	$("input[name='job_id']").val($USER_JOBS[0].job_id);
	$("input[name='user_id']").val($USER_JOBS[0].employer.ID);
	$("button.job_name").text($USER_JOBS[0].job_name);
	$("button.user_name").text($USER_JOBS[0].employer.Name);
});