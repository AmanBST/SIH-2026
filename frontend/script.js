/* ============================================
   PAGE NAVIGATION
============================================ */

function showPage(pageId) {

    // Hide all pages
    const pages = document.querySelectorAll(".page");

    pages.forEach(page => {
        page.classList.remove("active-page");
    });


    // Show selected page
    const selectedPage = document.getElementById(pageId);

    if (selectedPage) {
        selectedPage.classList.add("active-page");
    }


    // Load profile when profile page opens
    if (pageId === "profile") {
        loadProfile();
    }


    // Remove active from all navigation items
    const navItems = document.querySelectorAll(".nav-item");

    navItems.forEach(item => {
        item.classList.remove("active");
    });


    // Activate only selected navigation item
    const selectedNav =
        document.getElementById("nav-" + pageId);

    if (selectedNav) {
        selectedNav.classList.add("active");
    }

}


/* ============================================
   IMAGE PREVIEW
============================================ */

function previewImage(event) {

    const file = event.target.files[0];

    if (!file) {
        return;
    }


    // Check file size
    const maxSize = 10 * 1024 * 1024;

    if (file.size > maxSize) {
        alert("File size must be less than 10 MB.");
        return;
    }


    // Check image
    if (!file.type.startsWith("image/")) {
        alert("Please select an image file.");
        return;
    }


    const reader = new FileReader();


    reader.onload = function(e) {

        const preview =
            document.getElementById("preview");

        const previewContainer =
            document.getElementById("preview-container");

        const analyzeButton =
            document.getElementById("analyzeButton");


        preview.src = e.target.result;

        previewContainer.style.display = "block";

        analyzeButton.style.display = "inline-flex";

        analyzeButton.disabled = false;


        // Save image for other pages
        localStorage.setItem(
            "productImage",
            e.target.result
        );

    };


    reader.readAsDataURL(file);

}


/* ============================================
   START ANALYSIS
============================================ */

function startAnalysis() {

    const image =
        localStorage.getItem("productImage");


    if (!image) {

        alert(
            "Please upload a product image first."
        );

        return;
    }


    // Put image into analysis page
    document.getElementById("analysisImage").src =
        image;


    // Move to analysis page
    showPage("analysis");


    // Start animation
    runAnalysis();

}


/* ============================================
   ANALYSIS ANIMATION
============================================ */

function runAnalysis() {

    const step1 =
        document.getElementById("step1Icon");

    const step2 =
        document.getElementById("step2Icon");

    const step3 =
        document.getElementById("step3Icon");

    const step4 =
        document.getElementById("step4Icon");


    // Step 1
    step1.innerHTML =
        '<i class="fa-solid fa-circle-check"></i>';


    setTimeout(function() {

        step2.innerHTML =
            '<i class="fa-solid fa-circle-check"></i>';


        setTimeout(function() {

            step3.innerHTML =
                '<i class="fa-solid fa-circle-check"></i>';


            setTimeout(function() {

                step4.innerHTML =
                    '<i class="fa-solid fa-circle-check"></i>';


                // After analysis
                setTimeout(function() {

                    loadResultImage();

                    showPage("result");

                }, 1000);


            }, 1200);


        }, 1200);


    }, 1000);

}


/* ============================================
   RESULT IMAGE
============================================ */

function loadResultImage() {

    const image =
        localStorage.getItem("productImage");


    if (image) {

        document.getElementById("resultImage").src =
            image;

    }

}


/* ============================================
   LEGAL RULE SEARCH
============================================ */

function searchRules() {

    const searchInput =
        document.getElementById("ruleSearch");

    const searchText =
        searchInput.value.toLowerCase().trim();

    const ruleCards =
        document.querySelectorAll(".rule-item");


    ruleCards.forEach(card => {

        const text =
            card.innerText.toLowerCase();


        if (text.includes(searchText)) {

            card.style.display = "flex";

        } else {

            card.style.display = "none";

        }

    });

}


/* ============================================
   LOGIN & SIGNUP - BACKEND CONNECTED
============================================ */

const API_URL =
    "http://127.0.0.1:8000";


/* ============================================
   SHOW LOGIN
============================================ */

function showLogin() {

    document.getElementById("loginPage").style.display =
        "flex";

    document.getElementById("signupPage").style.display =
        "none";

}


/* ============================================
   SHOW SIGNUP
============================================ */

function showSignup() {

    document.getElementById("loginPage").style.display =
        "none";

    document.getElementById("signupPage").style.display =
        "flex";

}


/* ============================================
   SIGNUP
============================================ */

async function signupUser(event) {

    event.preventDefault();


    const name =
        document.getElementById("signupName").value.trim();

    const email =
        document.getElementById("signupEmail").value.trim();

    const password =
        document.getElementById("signupPassword").value;

    const confirmPassword =
        document.getElementById(
            "signupConfirmPassword"
        ).value;


    /* PASSWORD MATCH */

    if (password !== confirmPassword) {

        alert("Passwords do not match.");

        return;
    }


    /* PASSWORD LENGTH */

    if (password.length < 6) {

        alert(
            "Password must contain at least 6 characters."
        );

        return;
    }


    try {

        const response = await fetch(
            `${API_URL}/api/signup`,
            {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    full_name: name,

                    email: email,

                    password: password

                })

            }
        );


        const data = await response.json();


        /* BACKEND ERROR */

        if (!response.ok || !data.success) {

            alert(
                data.message ||
                "Unable to create account."
            );

            return;
        }


        /*
           SAVE ONLY USER INFORMATION.

           Password is NOT saved here.
        */

        localStorage.setItem(
            "legalScanUser",
            JSON.stringify(data.user)
        );


        alert(
            "Account created successfully! Please sign in."
        );


        /* CLEAR FORM */

        document.getElementById("signupName").value =
            "";

        document.getElementById("signupEmail").value =
            "";

        document.getElementById("signupPassword").value =
            "";

        document.getElementById(
            "signupConfirmPassword"
        ).value = "";


        /* OPEN LOGIN */

        showLogin();


    } catch (error) {

        console.error(
            "Signup error:",
            error
        );

        alert(
            "Cannot connect to LegalScan server. " +
            "Please make sure the backend is running."
        );

    }

}


/* ============================================
   LOGIN
============================================ */

async function loginUser(event) {

    event.preventDefault();


    const email =
        document.getElementById("loginEmail").value.trim();

    const password =
        document.getElementById("loginPassword").value;


    try {

        const response = await fetch(
            `${API_URL}/api/login`,
            {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    email: email,

                    password: password

                })

            }
        );


        const data = await response.json();


        /* LOGIN FAILED */

        if (!response.ok || !data.success) {

            alert(
                data.message ||
                "Incorrect email or password."
            );

            return;
        }


        /*
           Save logged-in user's information.
        */

        localStorage.setItem(
            "legalScanUser",
            JSON.stringify(data.user)
        );


        /* HIDE LOGIN */

        document.getElementById("loginPage").style.display =
            "none";


        /* UPDATE SIDEBAR */

        updateUserDisplay(data.user);


        /* LOAD PROFILE */

        loadProfile();


        /* OPEN DASHBOARD */

        showPage("dashboard");


        /* CLEAR LOGIN FORM */

        document.getElementById("loginEmail").value =
            "";

        document.getElementById("loginPassword").value =
            "";


    } catch (error) {

        console.error(
            "Login error:",
            error
        );

        alert(
            "Cannot connect to LegalScan server. " +
            "Please make sure the backend is running."
        );

    }

}


/* ============================================
   UPDATE USER DISPLAY
============================================ */

function updateUserDisplay(user) {

    if (!user) {
        return;
    }


    /* SIDEBAR NAME */

    const userNames =
        document.querySelectorAll(
            ".user-card strong"
        );


    userNames.forEach(element => {

        element.textContent =
            user.full_name;

    });


    /* SIDEBAR AVATAR */

    const userAvatar =
        document.querySelector(".user-avatar");


    if (userAvatar && user.full_name) {

        userAvatar.textContent =
            user.full_name
                .charAt(0)
                .toUpperCase();

    }

}


/* ============================================
   PASSWORD VISIBILITY
============================================ */

function togglePassword(inputId, icon) {

    const input =
        document.getElementById(inputId);


    if (input.type === "password") {

        input.type = "text";

        icon.classList.remove("fa-eye");

        icon.classList.add("fa-eye-slash");

    } else {

        input.type = "password";

        icon.classList.remove("fa-eye-slash");

        icon.classList.add("fa-eye");

    }

}


/* ============================================
   PROFILE
============================================ */

function loadProfile() {

    const savedUser =
        localStorage.getItem("legalScanUser");


    if (!savedUser) {
        return;
    }


    const user =
        JSON.parse(savedUser);


    /*
       IMPORTANT:

       Backend returns:

       user.full_name

       NOT:

       user.name
    */


    /* PROFILE NAME */

    const profileName =
        document.getElementById("profileName");

    const profileFullName =
        document.getElementById(
            "profileFullName"
        );


    if (profileName) {

        profileName.textContent =
            user.full_name;

    }


    if (profileFullName) {

        profileFullName.textContent =
            user.full_name;

    }


    /* EMAIL */

    const profileEmail =
        document.getElementById("profileEmail");

    const profileEmailDetail =
        document.getElementById(
            "profileEmailDetail"
        );


    if (profileEmail) {

        profileEmail.textContent =
            user.email;

    }


    if (profileEmailDetail) {

        profileEmailDetail.textContent =
            user.email;

    }


    /* AVATAR */

    const avatar =
        document.getElementById("profileAvatar");


    if (avatar && user.full_name) {

        avatar.textContent =
            user.full_name
                .charAt(0)
                .toUpperCase();

    }


    /* UPDATE SIDEBAR */

    updateUserDisplay(user);

}


/* ============================================
   LOGOUT
============================================ */

function logoutUser() {

    const confirmLogout =
        confirm(
            "Are you sure you want to logout?"
        );


    if (!confirmLogout) {
        return;
    }


    /*
       Remove logged-in user.
    */

    localStorage.removeItem(
        "legalScanUser"
    );


    /* Open login */

    showLogin();

}


/* ============================================
   EDIT FULL NAME
============================================ */

function editFullName() {

    const savedUser =
        localStorage.getItem("legalScanUser");


    if (!savedUser) {
        return;
    }


    const user =
        JSON.parse(savedUser);


    const newName =
        prompt(
            "Enter your new full name:",
            user.full_name
        );


    /* Cancel pressed */

    if (newName === null) {
        return;
    }


    const trimmedName =
        newName.trim();


    /* Empty name */

    if (trimmedName === "") {

        alert(
            "Name cannot be empty."
        );

        return;
    }


    /*
       TEMPORARY FRONTEND UPDATE

       We will connect this to the
       FastAPI database next.
    */

    user.full_name =
        trimmedName;


    localStorage.setItem(
        "legalScanUser",
        JSON.stringify(user)
    );


    /* Refresh profile */

    loadProfile();


    alert(
        "Full name updated successfully."
    );

}


/* ============================================
   INITIAL PAGE
============================================ */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        /*
           If a user is already logged in,
           show dashboard.

           Otherwise show login.
        */

        const savedUser =
            localStorage.getItem(
                "legalScanUser"
            );


        if (savedUser) {

            try {

                const user =
                    JSON.parse(savedUser);

                updateUserDisplay(user);

                loadProfile();

                showPage("dashboard");

            } catch (error) {

                localStorage.removeItem(
                    "legalScanUser"
                );

                showLogin();

            }

        } else {

            showLogin();

        }

    }
);
