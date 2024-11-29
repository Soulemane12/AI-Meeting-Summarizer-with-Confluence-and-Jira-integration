document.addEventListener('DOMContentLoaded', function() {
    const summarizeForm = document.getElementById('summarize-form');
    const nameFilter = document.getElementById('name-filter');
    const audioFileInput = document.getElementById('audio-file');
    let allActionItems = [];

    summarizeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        var transcript = document.getElementById('transcript').value;
        var audioFile = audioFileInput.files[0];
        
        if (audioFile) {
            const formData = new FormData();
            formData.append('audio', audioFile);
            
            fetch('/transcribe', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error:', data.error);
                    alert('Error transcribing audio: ' + data.error);
                    return;
                }
                document.getElementById('transcript').value = data.transcript;
                summarizeTranscript(data.transcript);
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('Error transcribing audio: ' + error);
            });
        } else if (transcript) {
            summarizeTranscript(transcript);
        } else {
            alert('Please enter a transcript or upload an audio file.');
        }
    });

    function summarizeTranscript(transcript) {
        fetch('/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({transcript: transcript}),
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('summary').textContent = data.summary;
            allActionItems = data.action_items;
            updateActionItems();
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }

    nameFilter.addEventListener('input', updateActionItems);

    function updateActionItems() {
        const actionItems = document.getElementById('action-items');
        actionItems.innerHTML = '';
        const filterName = nameFilter.value.toLowerCase();
        
        for (const item of allActionItems) {
            if (filterName === '' || item.assignee.toLowerCase().includes(filterName)) {
                const li = document.createElement('li');
                li.innerHTML = `<strong>${item.task}</strong> - Assigned to: ${item.assignee}, Due: ${item.due_date}`;
                
                const actionButton = document.createElement('button');
                actionButton.textContent = getActionButtonText(item.task);
                actionButton.onclick = () => performAction(item);
                
                li.appendChild(actionButton);
                actionItems.appendChild(li);
            }
        }
    }

    function getActionButtonText(task) {
        if (task.toLowerCase().includes('email')) return 'Send Email';
        if (task.toLowerCase().includes('remind')) return 'Set Reminder';
        return 'Copy';
    }
   
    function performAction(item) {
        const action = getActionButtonText(item.task);
        switch(action) {
            case 'Send Email':
                fetch('/generate_email', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(item),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error generating email:', data.error);
                        return;
                    }
                    const emailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(item.assignee)}&su=${encodeURIComponent(data.subject)}&body=${encodeURIComponent(data.body)}`;
                    window.open(emailUrl, '_blank');
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
                break;
            case 'Set Reminder':
                const reminderUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(item.task)}&details=${encodeURIComponent(`Assigned to: ${item.assignee}`)}&dates=${formatDateForGoogleCalendar(item.due_date)}`;
                window.open(reminderUrl, '_blank');
                break;
            case 'Copy':
                copyToClipboard(item);
                break;
        }
    }

    function copyToClipboard(item) {
        const text = `Task: ${item.task}\nAssigned to: ${item.assignee}\nDue: ${item.due_date}`;
        navigator.clipboard.writeText(text).then(() => {
            alert('Task copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy text: ', err);
        });
    }

    function formatDateForGoogleCalendar(dateString) {
        const date = new Date(dateString);
        const formattedDate = date.toISOString().replace(/-|:|\.\d\d\d/g, "");
        return `${formattedDate}/${formattedDate}`;
    }
});

