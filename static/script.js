// Get the select elements for start time and end time
var startTimeSelect = document.getElementById("start-time");
var endTimeSelect = document.getElementById("end-time");
var editstartTimeSelect = document.getElementById("edit-start");
var editendTimeSelect = document.getElementById("edit-end");

// Loop to generate options for all 24 hours
for (var i = 0; i < 24; i++) {
    var hour = (i < 10 ? '0' : '') + i + ":00"; // Add leading zero for single-digit hours
    
    // Create options for both start and end time
    var startOption = new Option(hour, hour);
    var endOption = new Option(hour, hour);
    var edit0ption = new Option(hour, hour);
    var edit20ption = new Option(hour, hour);
    
    // Append options to their respective select elements
    startTimeSelect.appendChild(startOption);
    endTimeSelect.appendChild(endOption);
    editstartTimeSelect.appendChild(edit0ption);
    editendTimeSelect.appendChild(edit20ption);
}

function done(taskId, taskDiff) {
    $.ajax({
        type: 'POST',
        url: '/complete_task',
        data: { taskId: taskId,
                taskDiff: taskDiff},
        success: function(response) {
            // Handle success response from Flask
            console.log(response);
            location.reload(); // Reload the page
        },
        error: function(xhr, status, error) {
            // Handle error response
            console.error(error);
        }
    });
}

function remove_task(taskIndex) {

    var imageId = taskIndex; // Assuming the image ID follows the pattern 'trash_can_' + taskIndex
    console.log(imageId)

    $.ajax({
        type: 'POST',
        url: '/perform_action',
        data: { imageId: imageId },
        success: function(response) {
            // Handle success response from Flask
            console.log(response);
            location.reload(); // Reload the page
        },
        error: function(xhr, status, error) {
            // Handle error response
            console.error(error);
        }
    });
}


function showCreateTask() {
    document.getElementById("createTaskSection").style.display = "block";
    document.getElementById("editTaskSection").style.display = "none";
    document.getElementById("editProfileSection").style.display = "none";
}

function showEditTask() {
    document.getElementById("createTaskSection").style.display = "none";
    document.getElementById("editTaskSection").style.display = "block";
    document.getElementById("editProfileSection").style.display = "none";
}

function showEditProfile() {
    document.getElementById("createTaskSection").style.display = "none";
    document.getElementById("editTaskSection").style.display = "none";
    document.getElementById("editProfileSection").style.display = "block";
}

document.getElementById('old-task').addEventListener('change', function() {
    var selectedOption = this.options[this.selectedIndex];
    document.getElementById('edit-task').value = selectedOption.getAttribute('data-taskname');
    document.getElementById('edit-start').value = selectedOption.getAttribute('data-taskstart');
    document.getElementById('edit-end').value = selectedOption.getAttribute('data-taskend');
});
