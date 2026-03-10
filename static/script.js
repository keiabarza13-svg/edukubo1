async function handleAuth() {
    const userField = document.getElementById('username').value;
    const passField = document.getElementById('password').value;
    const fullNameField = document.getElementById('full_name') ? document.getElementById('full_name').value : "";
    const gradeField = document.getElementById('grade_level') ? document.getElementById('grade_level').value : 1;

    // Determine the correct URL based on selection
    let endpoint = '/login';
    if (currentMode === 'register') {
        endpoint = (selectedRole === 'Student') ? '/register/student' : '/register/teacher';
    }

    const payload = {
        username: userField,
        password: passField,
        full_name: fullNameField,
        grade_level: gradeField,
        role: selectedRole.toLowerCase()
    };

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const res = await response.json();

        if (res.success) {
            alert("Success: " + res.message);
            
            if (currentMode === 'register') {
                // TEST STEP: Go back to login view after registering
                toggleMode(); 
                document.getElementById('username').value = "";
                document.getElementById('password').value = "";
            } else {
                // TEST STEP: Redirect on successful login
                window.location.href = (res.role === 'student') ? '/dashboard/student' : '/dashboard/teacher';
            }
        } else {
            // TEST STEP: This will show "User not found" or "Incorrect password"
            alert("Auth Failed: " + res.message);
        }
    } catch (error) {
        alert("Connection Error: Could not reach the server.");
    }
}