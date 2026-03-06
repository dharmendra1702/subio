document.addEventListener("DOMContentLoaded", () => {

const csrftoken = getCookie("csrftoken");
let cart = {};


/* ================= CSRF ================= */

function getCookie(name){

let cookieValue = null;

if(document.cookie && document.cookie !== ''){

const cookies = document.cookie.split(';');

for(let cookie of cookies){

cookie = cookie.trim();

if(cookie.startsWith(name + '=')){
cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
break;
}

}

}

return cookieValue;

}


/* ================= LOAD CART ================= */

async function loadCart(){

const res = await fetch("/cart-json/");
const data = await res.json();

cart = {};

data.items.forEach(item=>{
cart[item.id] = item;
});

updateCartCount();
updateDrawer();
syncProductCards();

}

loadCart();


/* ================= CART COUNT ================= */

function updateCartCount(){

let count = 0;

Object.values(cart).forEach(i=>{
count += i.quantity;
});

const el = document.getElementById("cartCount");

if(el) el.innerText = count;

}


/* ================= DRAWER ================= */

function updateDrawer(){

let html = "";
let total = 0;

Object.values(cart).forEach(item=>{

total += item.price * item.quantity;

html += `
<div class="drawer-item">
<img src="${item.image}">
<div class="drawer-info">
<p>${item.name}</p>
<p>₹${item.price} × ${item.quantity}</p>
</div>
</div>
`;

});

const items = document.getElementById("drawerItems");
const totalEl = document.getElementById("drawerTotal");

if(items) items.innerHTML = html;
if(totalEl) totalEl.innerText = total.toFixed(2);

}


/* ================= SYNC PRODUCT CARDS ================= */

function syncProductCards(){

document.querySelectorAll(".add-to-cart-form").forEach(form=>{

const id = form.querySelector("input[name='product_id']").value;

const qty = form.querySelector(".qty");
const addBtn = form.querySelector(".add-btn");
const qtyBox = form.querySelector(".qty-box");

if(cart[id]){

qty.innerText = cart[id].quantity;

addBtn.style.display="none";
qtyBox.style.display="flex";

}else{

addBtn.style.display="block";
qtyBox.style.display="none";

}

});

}


/* ================= SERVER SYNC ================= */

function syncServer(productId,action){

fetch(UPDATE_CART_URL,{
method:"POST",
headers:{
"Content-Type":"application/x-www-form-urlencoded",
"X-CSRFToken":csrftoken
},
body:`product_id=${productId}&action=${action}`
});

}


/* ================= BUTTONS ================= */

document.querySelectorAll(".add-to-cart-form").forEach(form=>{

const addBtn = form.querySelector(".add-btn");
const plus = form.querySelector(".plus");
const minus = form.querySelector(".minus");

const id = form.querySelector("input[name='product_id']").value;

const name = document.querySelector(`[data-product-name="${id}"]`)?.innerText;
const price = parseFloat(document.querySelector(`[data-product-price="${id}"]`)?.innerText);
const image = document.querySelector(`[data-product-image="${id}"]`)?.src;


/* ADD */

if(addBtn){

addBtn.onclick = () => {

cart[id] = {
id,
name,
price,
image,
quantity:1
};

updateCartCount();
updateDrawer();
syncProductCards();

syncServer(id,"add");

};

}


/* PLUS */

if(plus){

plus.onclick = () => {

if(!cart[id]) return;

cart[id].quantity++;

updateCartCount();
updateDrawer();
syncProductCards();

syncServer(id,"increase");

};

}


/* MINUS */

if(minus){

minus.onclick = () => {

if(!cart[id]) return;

cart[id].quantity--;

if(cart[id].quantity <= 0){
delete cart[id];
}

updateCartCount();
updateDrawer();
syncProductCards();

syncServer(id,"decrease");

};

}

});


/* ================= DRAWER ================= */

window.openCart = function(){

document.getElementById("cartDrawer").classList.add("open");
document.getElementById("cartOverlay").classList.add("show");

updateDrawer();

}

window.closeCart = function(){

document.getElementById("cartDrawer").classList.remove("open");
document.getElementById("cartOverlay").classList.remove("show");

}

});