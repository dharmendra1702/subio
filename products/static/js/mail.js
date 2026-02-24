// ===== Django CSRF Safe Fetch =====
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute("content");
}

// ===== Newsletter Submit =====
document.getElementById("newsletterForm").addEventListener("submit", function(e){

    e.preventDefault();

    const formData = new FormData(this);

    fetch("/newsletter/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),   // ALWAYS fresh token
        },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
    });

});