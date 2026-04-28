(function(){

// 🚫 STOP duplicate execution
if (window.__navbarLoaded) return;
window.__navbarLoaded = true;

/* ==========================================
   NAVBAR SCROLL EFFECT
========================================== */

const navbar = document.querySelector(".navbar");

if (navbar) {
  window.addEventListener("scroll", () => {
    navbar.classList.toggle("scrolled", window.scrollY > 60);
  });
}

/* ==========================================
   DOM READY
========================================== */

document.addEventListener("DOMContentLoaded", () => {

  /* ===== DESKTOP PROFILE ===== */
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

  /* ===== ACCOUNT DROPDOWN ===== */
  const accountBtn = document.getElementById("accountBtn");
  const accountDropdown = document.getElementById("accountDropdown");

  if (accountBtn && accountDropdown) {
    accountBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      accountDropdown.classList.toggle("show");
    });

    document.addEventListener("click", () => {
      accountDropdown.classList.remove("show");
    });
  }

  /* ===== MOBILE MENU ===== */
  const hamburger = document.getElementById("hamburger");
  const mobileMenu = document.getElementById("mobileMenu");

  if (hamburger && mobileMenu) {
    hamburger.addEventListener("click", (e) => {
      e.stopPropagation();
      mobileMenu.classList.toggle("show");
      hamburger.classList.toggle("active");
    });

    document.addEventListener("click", () => {
      mobileMenu.classList.remove("show");
      hamburger.classList.remove("active");
    });

    mobileMenu.addEventListener("click", e => e.stopPropagation());
  }

  /* ===== MOBILE ACCOUNT ===== */
  const mobileAccountBtn = document.getElementById("mobileAccountBtn");
  const mobileAccountDropdown = document.getElementById("mobileAccountDropdown");

  if (mobileAccountBtn && mobileAccountDropdown) {
    mobileAccountBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      mobileAccountDropdown.classList.toggle("show");
    });

    document.addEventListener("click", () => {
      mobileAccountDropdown.classList.remove("show");
    });
  }

  /* ===== LOGOUT ===== */
  const logoutBtn = document.getElementById("logoutBtn");
  const logoutBtnMobile = document.getElementById("logoutBtnMobile");
  const logoutModal = document.getElementById("logoutModal");
  const cancelLogout = document.getElementById("cancelLogout");
  const confirmLogoutBtn = document.getElementById("confirmLogout");

  if (logoutBtn && logoutModal) {
    logoutBtn.onclick = () => logoutModal.style.display = "flex";
  }

  if (logoutBtnMobile && logoutModal) {
    logoutBtnMobile.onclick = () => logoutModal.style.display = "flex";
  }

  if (cancelLogout && logoutModal) {
    cancelLogout.onclick = () => logoutModal.style.display = "none";
  }

  if (confirmLogoutBtn) {
    confirmLogoutBtn.onclick = () => {
      const form = document.getElementById("logoutForm");
      if (form) form.submit();
    };
  }

});

})();