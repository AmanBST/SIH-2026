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

    const selectedPage =
        document.getElementById(pageId);

    if (selectedPage) {

        selectedPage.classList.add("active-page");

    }
    if (pageId === "profile") {

    loadProfile();

}

    // Remove active from all navigation items

    const navItems =
        document.querySelectorAll(".nav-item");

    navItems.forEach(item => {

        item.classList.remove("active");

    });


    // Activate only the selected navigation item

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

        const preview = document.getElementById("preview");

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

        alert("Please upload a product image first.");

        return;

    }


    // Put image into analysis page

    document.getElementById("analysisImage").src = image;


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
   INITIAL PAGE
============================================ */

document.addEventListener("DOMContentLoaded", function() {

    // Start with login page

    showLogin();

});
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
   LOGIN & SIGNUP
============================================ */


/* SHOW LOGIN */

function showLogin() {

    document.getElementById("loginPage").style.display =
        "flex";

    document.getElementById("signupPage").style.display =
        "none";

}


/* SHOW SIGNUP */

function showSignup() {

    document.getElementById("loginPage").style.display =
        "none";

    document.getElementById("signupPage").style.display =
        "flex";

}


/* SIGNUP */

function signupUser(event) {

    event.preventDefault();


    const name =
        document.getElementById("signupName").value.trim();

    const email =
        document.getElementById("signupEmail").value.trim();

    const password =
        document.getElementById("signupPassword").value;

    const confirmPassword =
        document.getElementById("signupConfirmPassword").value;


    // Check passwords

    if (password !== confirmPassword) {

        alert("Passwords do not match.");

        return;

    }


    // Basic password validation

    if (password.length < 6) {

        alert("Password must contain at least 6 characters.");

        return;

    }


    // Save demo account

    const user = {

        name: name,

        email: email,

        password: password

    };


    localStorage.setItem(
        "legalScanUser",
        JSON.stringify(user)
    );


    alert(
        "Account created successfully! Please sign in."
    );


    showLogin();

}


/* LOGIN */

function loginUser(event) {

    event.preventDefault();


    const email =
        document.getElementById("loginEmail").value.trim();

    const password =
        document.getElementById("loginPassword").value;


    const savedUser =
        localStorage.getItem("legalScanUser");


    if (!savedUser) {

        alert(
            "No account found. Please create an account first."
        );

        return;

    }


    const user =
        JSON.parse(savedUser);


    if (
        email === user.email &&
        password === user.password
    ) {

        // Hide login

        document.getElementById("loginPage").style.display =
            "none";


        // Update inspector name

        const userNames =
            document.querySelectorAll(".user-card strong");


        userNames.forEach(element => {

            element.textContent = user.name;

        });


        // Open dashboard

        showPage("dashboard");


    } else {

        alert(
            "Incorrect email or password."
        );

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


    // Profile name

    const profileName =
        document.getElementById("profileName");

    const profileFullName =
        document.getElementById("profileFullName");


    if (profileName) {

        profileName.textContent = user.name;

    }

    if (profileFullName) {

        profileFullName.textContent = user.name;

    }


    // Email

    const profileEmail =
        document.getElementById("profileEmail");

    const profileEmailDetail =
        document.getElementById("profileEmailDetail");


    if (profileEmail) {

        profileEmail.textContent = user.email;

    }

    if (profileEmailDetail) {

        profileEmailDetail.textContent = user.email;

    }


    // Avatar

    const avatar =
        document.getElementById("profileAvatar");

    if (avatar && user.name) {

        avatar.textContent =
            user.name.charAt(0).toUpperCase();

    }

}


/* ============================================
   LOGOUT
============================================ */

function logoutUser() {

    const confirmLogout =
        confirm("Are you sure you want to logout?");

    if (!confirmLogout) {

        return;

    }


    // Hide profile/dashboard

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
            user.name
        );


    // Cancel pressed

    if (newName === null) {

        return;

    }


    const trimmedName =
        newName.trim();


    // Empty name

    if (trimmedName === "") {

        alert("Name cannot be empty.");

        return;

    }


    // Update name

    user.name = trimmedName;


    // Save updated user

    localStorage.setItem(
        "legalScanUser",
        JSON.stringify(user)
    );


    // Refresh profile

    loadProfile();


    alert("Full name updated successfully.");

}