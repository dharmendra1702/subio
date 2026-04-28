/* ================= CSRF ================= */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/* ================= UPDATE CART ================= */
function updateCartQty(productId, variantId, change){

    const qtyBox = document.getElementById(`qty-box-${productId}-${variantId}`)
    const addBtn = document.getElementById(`add-btn-${productId}-${variantId}`)
    const qtyVal = document.getElementById(`qty-val-${productId}-${variantId}`)

    let currentQty = parseInt(qtyVal?.innerText || "0")
    let newQty = currentQty + change

    if(newQty < 0) newQty = 0

    /* ===== UI UPDATE (INSTANT) ===== */
    if(qtyBox && addBtn && qtyVal){
        if(newQty > 0){
            qtyBox.style.display = "flex"
            addBtn.style.display = "none"
            qtyVal.innerText = newQty
        }else{
            qtyBox.style.display = "none"
            addBtn.style.display = "block"
            qtyVal.innerText = 0
        }
    }

    /* ===== BACKEND SYNC (SAFE FORMAT) ===== */
    let action = "add"
    if(change > 0 && currentQty > 0) action = "increase"
    if(change < 0) action = "decrease"

    fetch("/update-cart/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: new URLSearchParams({
            product_id: productId,
            variant_id: variantId,
            action: action
        })
    })
    .then(res => res.json())
    .then(data => {

        /* ===== TRUST BACKEND ===== */
        if (typeof renderDrawer === "function") {
            renderDrawer(data)
        }

        /* ===== NAVBAR ===== */
        const cartCount = document.getElementById("cartCount")
        if(cartCount){
            cartCount.innerText = data.cart_count || 0
        }

        /* ===== FIX UI BASED ON SERVER ===== */
        const item = data.items.find(i =>
            String(i.product_id) === String(productId) &&
            String(i.variant_id) === String(variantId)
        )

        if(qtyBox && addBtn && qtyVal){
            if(item){
                qtyBox.style.display = "flex"
                addBtn.style.display = "none"
                qtyVal.innerText = item.quantity
            } else {
                qtyBox.style.display = "none"
                addBtn.style.display = "block"
                qtyVal.innerText = 0
            }
        }
    })
    .catch(err => {
        console.error("Cart update failed:", err)

        // ❗ rollback UI
        location.reload()
    })
}

/* ================= INITIAL LOAD ================= */
document.addEventListener("DOMContentLoaded", () => {

    fetch("/cart-json/")
    .then(res => res.json())
    .then(data => {

        /* ===== DRAWER ===== */
        if (typeof renderDrawer === "function") {
            renderDrawer(data)
        }

        /* ===== NAVBAR ===== */
        const cartCount = document.getElementById("cartCount")
        if(cartCount){
            cartCount.innerText = data.cart_count || 0
        }

        /* ===== PRODUCT GRID SYNC ===== */
        data.items.forEach(item => {

            const productId = item.product_id
            const variantId = item.variant_id

            const qtyBox = document.getElementById(`qty-box-${productId}-${variantId}`)
            const addBtn = document.getElementById(`add-btn-${productId}-${variantId}`)
            const qtyVal = document.getElementById(`qty-val-${productId}-${variantId}`)

            if(qtyBox && addBtn && qtyVal){
                qtyBox.style.display = "flex"
                addBtn.style.display = "none"
                qtyVal.innerText = item.quantity
            }
        })
    })
    .catch(err => console.error("Cart load failed:", err))
})

/* ================= GLOBAL ================= */
window.updateCartQty = updateCartQty;

/* ================= FILTER FUNCTIONS ================= */
window.toggleFilters = function () {
    const box = document.getElementById("filterBox");
    if (box) box.classList.toggle("active");
};

window.searchProducts = function () {
    const input = document.getElementById("search");
    const cards = document.querySelectorAll(".card");

    const value = input.value.toLowerCase();

    cards.forEach(card => {
        const name = card.dataset.name || "";
        card.style.display = name.includes(value) ? "block" : "none";
    });
};

window.sortProducts = function(type){};

window.clearFilters = function(){
    location.reload();
};

window.filterStock = function(){};
window.filterWeight = function(){};
window.filterPrice = function(val){
    document.getElementById("priceVal").innerText = val;
};