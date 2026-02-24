const profileBtn = document.getElementById("profileBtn");
const profileMenu = document.getElementById("profileMenu");

profileBtn.addEventListener("click",()=>{
 profileMenu.style.display =
 profileMenu.style.display === "flex" ? "none" : "flex";
});

profileBtn.onclick = () => {
  profileMenu.classList.toggle("show");
};

document.addEventListener("click", (e) => {
  if (!e.target.closest(".profile-wrapper")) {
    profileMenu.classList.remove("show");
  }
});

const logoutBtn = document.getElementById("logoutBtn");
const modal = document.getElementById("logoutModal");
const cancel = document.getElementById("cancelLogout");
const confirm = document.getElementById("confirmLogout");

logoutBtn.onclick = () => modal.style.display = "flex";
cancel.onclick = () => modal.style.display = "none";

confirm.onclick = () => {
  document.getElementById("logoutForm").submit();
};