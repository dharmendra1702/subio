document.addEventListener("DOMContentLoaded", function () {

  const grid = document.getElementById('grid');
  const searchInput = document.getElementById('search');

  let activeCategory = "all";
  let maxPrice = Infinity;
  let minWeight = "";
  let inStock = false;

  function getCards() {
    return document.querySelectorAll('.card');
  }

  function extractWeight(weightText) {
    const match = weightText.match(/\d+/);
    return match ? parseInt(match[0]) : 0;
  }

  function applyFilters() {

    const cards = getCards();

    cards.forEach(card => {

      let show = true;

      const cardCategory = card.dataset.cat;
      const cardPrice = parseFloat(card.dataset.price);
      const cardWeight = extractWeight(card.dataset.weight);
      const cardName = card.dataset.name.toLowerCase();
      const stockValue = parseInt(card.dataset.stock) || 0;

      // CATEGORY
      if (activeCategory !== "all" && cardCategory != activeCategory) {
        show = false;
      }

      // SEARCH
      if (searchInput.value.trim() !== "") {
        show = show && cardName.includes(searchInput.value.toLowerCase());
      }

      // PRICE
      show = show && cardPrice <= maxPrice;

      // WEIGHT
      if (minWeight !== "") {
        show = show && cardWeight >= parseInt(minWeight);
      }

      // STOCK
      if (inStock) {
        show = show && stockValue > 0;
      }

      card.classList.toggle("hide", !show);
    });
  }

  window.filterCat = function (cat, el) {
    activeCategory = String(cat);

    document.querySelectorAll(".cat-circle")
      .forEach(c => c.classList.remove("active"));

    el.classList.add("active");

    applyFilters();
  };

  window.searchProducts = function () {
    applyFilters();
  };

  window.sortProducts = function (type) {

    const cardsArray = Array.from(getCards());

    if (type === "relevance") {
      location.reload();
      return;
    }

    if (type === "low") {
      cardsArray.sort((a, b) =>
        parseFloat(a.dataset.price) - parseFloat(b.dataset.price)
      );
    }

    if (type === "high") {
      cardsArray.sort((a, b) =>
        parseFloat(b.dataset.price) - parseFloat(a.dataset.price)
      );
    }

    if (type === "name") {
      cardsArray.sort((a, b) =>
        a.dataset.name.localeCompare(b.dataset.name)
      );
    }

    cardsArray.forEach(card => grid.appendChild(card));
  };

  window.filterPrice = function (value) {
    maxPrice = parseFloat(value);
    document.getElementById("priceVal").innerText = value;
    applyFilters();
  };

  window.filterWeight = function (value) {
    minWeight = value;
    applyFilters();
  };

  window.filterStock = function (checkbox) {
    inStock = checkbox.checked;
    applyFilters();
  };

  window.clearFilters = function () {

    activeCategory = "all";
    maxPrice = Infinity;
    minWeight = "";
    inStock = false;
    searchInput.value = "";

    document.querySelectorAll(".cat-circle")
      .forEach(c => c.classList.remove("active"));

    document.querySelector(".cat-circle").classList.add("active");

    document.getElementById("priceVal").innerText = "2000";

    applyFilters();
  };

  window.wish = function (el) {
    el.classList.toggle("active");
    el.innerHTML = el.classList.contains("active") ? "❤" : "♡";
  };

  window.toggleFilters = function () {
    document.getElementById("filterBox").classList.toggle("active");
  };

});

document.addEventListener("DOMContentLoaded", function() {

    const selectedCategory = "{{ selected_category|default:'' }}";

    if(selectedCategory) {

        const circles = document.querySelectorAll(".cat-circle");

        circles.forEach(circle => {
            const onclickValue = circle.getAttribute("onclick");

            if(onclickValue && onclickValue.includes(selectedCategory)) {
                circle.click();  // 🔥 trigger existing filter system
            }
        });
    }

});