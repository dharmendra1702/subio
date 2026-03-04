document.querySelectorAll(".add-to-cart-form").forEach(form => {

    const addBtn = form.querySelector(".add-btn");
    const qtyBox = form.querySelector(".qty-box");
    const plus = form.querySelector(".plus");
    const minus = form.querySelector(".minus");
    const qtySpan = form.querySelector(".qty");

    let quantity = 1;

    addBtn.addEventListener("click", function(){
        addBtn.style.display = "none";
        qtyBox.style.display = "flex";
        sendToCart(form, quantity);
    });

    plus.addEventListener("click", function(){
        quantity++;
        qtySpan.innerText = quantity;
        sendToCart(form, quantity);
    });

    minus.addEventListener("click", function(){
        quantity--;

        if(quantity <= 0){
            quantity = 0;
            qtyBox.style.display = "none";
            addBtn.style.display = "block";
            sendToCart(form, 0);
        } else {
            qtySpan.innerText = quantity;
            sendToCart(form, quantity);
        }
    });

});

function sendToCart(form, quantity){

    const formData = new FormData(form);
    formData.append("quantity", quantity);

    fetch(ADD_TO_CART_URL, {
        method: "POST",
        headers: {
            "X-CSRFToken": form.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {

        if(data.status === "success"){
            const cartLink = document.querySelector(".nav-cart");
            if(cartLink){
                cartLink.innerText = "Cart (" + data.cart_count + ")";
            }
        }
    });
}

let cartLoading = false;

async function updateCart(productId, action){

if(cartLoading) return;
cartLoading = true;

try{

const res = await fetch("/update-cart/",{
method:"POST",
headers:{
"X-CSRFToken":getCookie("csrftoken"),
"Content-Type":"application/x-www-form-urlencoded"
},
body:`product_id=${productId}&action=${action}`
})

const data = await res.json()

if(data.status==="success"){

document.getElementById("subtotal").innerText=data.total

}

}catch(err){
console.error(err)
}

cartLoading=false

}

function updateCartCount(count){

const cartEl = document.querySelector(".nav-cart")

if(!cartEl) return

cartEl.innerText = `Cart (${count})`

cartEl.classList.add("cart-bounce")

setTimeout(()=>{
cartEl.classList.remove("cart-bounce")
},300)

}

function openCart(){

document.getElementById("cartDrawer").classList.add("open")
document.getElementById("cartOverlay").classList.add("show")

loadDrawerCart()

}

function closeCart(){

document.getElementById("cartDrawer").classList.remove("open")
document.getElementById("cartOverlay").classList.remove("show")

}


/* LOAD CART DATA */

async function loadDrawerCart(){

const res = await fetch("/cart-json/")
const data = await res.json()

let html=""
let total=0

data.items.forEach(item=>{

total += item.price * item.quantity

html+=`
<div class="drawer-item">

<img src="${item.image}">

<div class="drawer-info">

<p class="drawer-name">${item.name}</p>

<p>₹${item.price} × ${item.quantity}</p>

</div>

</div>
`

})

document.getElementById("drawerItems").innerHTML = html
document.getElementById("drawerTotal").innerText = total.toFixed(2)

}

document.querySelectorAll(".add-btn").forEach(btn=>{

btn.addEventListener("click",async function(){

const form=this.closest("form")
const productId=form.querySelector("input[name='product_id']").value

const res=await fetch(ADD_TO_CART_URL,{
method:"POST",
headers:{
"X-CSRFToken":getCookie("csrftoken"),
"Content-Type":"application/x-www-form-urlencoded"
},
body:`product_id=${productId}`
})

const data=await res.json()

if(data.status==="success"){

document.getElementById("cartCount").innerText=data.cart_count

showPopup("Added to cart")

openCart()

}

})

})