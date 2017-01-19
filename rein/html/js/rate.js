function setUser() {
	// Ensures valid content of the "User id" field and its label upon init and job change
	user_id = ''
	user_name = ''
	if ($CURRENT_USER == 0) {
		user_id = $USER_JOBS[$CURRENT_JOB].employer.SIN;
		user_name = $USER_JOBS[$CURRENT_JOB].employer.Name;
	} else if ($CURRENT_USER == 1) {
		user_id = $USER_JOBS[$CURRENT_JOB].mediator.SIN;
		user_name = $USER_JOBS[$CURRENT_JOB].mediator.Name;
	} else {
		user_id = $USER_JOBS[$CURRENT_JOB].employee.SIN;
		user_name = $USER_JOBS[$CURRENT_JOB].employee.Name;
	}
	if (user_id == $USER_ID) {
		if ($CURRENT_USER != 2) {
			return nextUser();
		}
		return lastUser();
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
	// Initialize contents of the job and user id fields and their labels
	$("input[name='rated_by_id']").val($USER_ID);
	$("input[name='job_id']").val($USER_JOBS[$CURRENT_JOB].job_id);
	$("button.job_name").text($USER_JOBS[$CURRENT_JOB].job_name);
	setUser();
});