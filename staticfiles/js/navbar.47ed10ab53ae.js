/* ==========================================
   NAVBAR SCROLL EFFECT
========================================== */

const navbar = document.querySelector(".navbar");

window.addEventListener("scroll", () => {
  if (window.scrollY > 60) {
    navbar.classList.add("scrolled");
  } else {
    navbar.classList.remove("scrolled");
  }
});


/* ==========================================
   DESKTOP ACCOUNT DROPDOWN
========================================== */

const profileBtn = document.getElementById("profileBtn");
const profileMenu = document.getElementById("profileMenu");

if (profileBtn && profileMenu) {

  profileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    profileMenu.classList.toggle("show");
  });

  document.addEventListener("click", () => {
    profileMenu.classList.remove("show");
  });
}


/* ==========================================
   MOBILE HAMBURGER DROPDOWN
========================================== */

document.addEventListener("DOMContentLoaded",()=>{

  const hamburger = document.getElementById("hamburger");
  const mobileMenu = document.getElementById("mobileMenu");

  if(!hamburger || !mobileMenu) return;

  // start closed
  mobileMenu.classList.remove("show");

  hamburger.addEventListener("click", e=>{
    e.stopPropagation();
    mobileMenu.classList.toggle("show");
    hamburger.classList.toggle("active");
  });

  document.addEventListener("click", ()=>{
    mobileMenu.classList.remove("show");
    hamburger.classList.remove("active");
  });

  mobileMenu.addEventListener("click", e=>{
    e.stopPropagation();
  });

});

document.addEventListener("DOMContentLoaded",()=>{

  const mobileAccountBtn = document.getElementById("mobileAccountBtn");
  const mobileAccountDropdown = document.getElementById("mobileAccountDropdown");

  if(mobileAccountBtn && mobileAccountDropdown){

    mobileAccountBtn.addEventListener("click", e=>{
      e.stopPropagation();
      mobileAccountDropdown.classList.toggle("show");
    });

    document.addEventListener("click", ()=>{
      mobileAccountDropdown.classList.remove("show");
    });

  }

});
/* ================= ACCOUNT DROPDOWN ================= */

const accountBtn = document.getElementById("accountBtn");
const accountDropdown = document.getElementById("accountDropdown");

if(accountBtn && accountDropdown){

  accountBtn.addEventListener("click", e=>{
    e.stopPropagation();
    accountDropdown.classList.toggle("show");
  });

  document.addEventListener("click", ()=>{
    accountDropdown.classList.remove("show");
  });

}


const logoutBtn = document.getElementById("logoutBtn");
const logoutBtnMobile = document.getElementById("logoutBtnMobile");
const logoutModal = document.getElementById("logoutModal");
const cancelLogout = document.getElementById("cancelLogout");
const confirmLogout = document.getElementById("confirmLogout");

if (logoutBtn) {
  logoutBtn.onclick = () => logoutModal.style.display = "flex";
}

if (logoutBtnMobile) {
  logoutBtnMobile.onclick = () => logoutModal.style.display = "flex";
}

cancelLogout.onclick = () => logoutModal.style.display = "none";

confirmLogout.onclick = () => {
  document.getElementById("logoutForm").submit();
};

