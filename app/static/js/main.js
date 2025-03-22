document.addEventListener('DOMContentLoaded', function() {
    // Dark mode toggle
    setupDarkMode();
    
    // Setup meal generation form
    setupMealGenerationForm();
    
    // Setup meal detail modal
    setupMealDetailModal();
});

// Dark Mode Toggle
function setupDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const htmlElement = document.querySelector('html');
    const bodyElement = document.querySelector('body');
    
    // Check for saved user preference
    const darkMode = localStorage.getItem('darkMode') === 'enabled';
    
    // Set initial dark mode state
    if (darkMode) {
        bodyElement.classList.add('dark-mode');
        if (darkModeToggle) darkModeToggle.checked = true;
    }
    
    // Add event listener for dark mode toggle
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', function() {
            if (this.checked) {
                bodyElement.classList.add('dark-mode');
                localStorage.setItem('darkMode', 'enabled');
            } else {
                bodyElement.classList.remove('dark-mode');
                localStorage.setItem('darkMode', 'disabled');
            }
        });
    }
}

// Meal Generation Form
function setupMealGenerationForm() {
    const mealForm = document.getElementById('mealGenerationForm');
    const loadingContainer = document.getElementById('loadingContainer');
    const mealsContainer = document.getElementById('mealSuggestions');
    
    if (mealForm) {
        mealForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading spinner
            if (loadingContainer) loadingContainer.classList.remove('d-none');
            if (mealsContainer) mealsContainer.classList.add('d-none');
            
            // Get form data
            const formData = new FormData(mealForm);
            const jsonData = {};
            formData.forEach((value, key) => {
                if (key === 'preferences') {
                    if (!jsonData[key]) jsonData[key] = [];
                    jsonData[key].push(value);
                } else {
                    jsonData[key] = value;
                }
            });
            
            // Send API request
            fetch('/api/generate-meal-plans', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => response.json())
            .then(data => {
                if (loadingContainer) loadingContainer.classList.add('d-none');
                if (mealsContainer) mealsContainer.classList.remove('d-none');
                
                if (data.success) {
                    displayMealSuggestions(data.meal_plans);
                } else {
                    showAlert(data.message || 'Failed to generate meal plans', 'danger');
                }
            })
            .catch(error => {
                if (loadingContainer) loadingContainer.classList.add('d-none');
                showAlert('An error occurred while generating meal plans', 'danger');
                console.error('Error:', error);
            });
        });
    }
}

// Display meal suggestions
function displayMealSuggestions(meals) {
    const mealsContainer = document.getElementById('mealSuggestions');
    const mealCardTemplate = document.getElementById('mealCardTemplate');
    
    if (!mealsContainer || !mealCardTemplate) return;
    
    // Clear previous meals
    mealsContainer.innerHTML = '';
    
    // Add meal cards
    meals.forEach(meal => {
        const mealCard = mealCardTemplate.content.cloneNode(true);
        
        // Set meal data
        mealCard.querySelector('.meal-title').textContent = meal.name;
        mealCard.querySelector('.meal-description').textContent = meal.description.substring(0, 100) + '...';
        mealCard.querySelector('.meal-price').textContent = 'KES ' + meal.price;
        mealCard.querySelector('.meal-calories').textContent = meal.nutrition.calories + ' kcal';
        
        // Set view details button
        const viewButton = mealCard.querySelector('.view-meal-details');
        viewButton.setAttribute('data-meal', JSON.stringify(meal));
        
        // Set save button
        const saveButton = mealCard.querySelector('.save-meal');
        saveButton.setAttribute('data-meal', JSON.stringify({
            name: meal.name,
            meal_type: document.getElementById('mealType').value,
            budget: document.getElementById('budget').value,
            preferences: Array.from(document.querySelectorAll('input[name="preferences"]:checked')).map(el => el.value),
            description: meal.description,
            ingredients: meal.ingredients,
            price: meal.price,
            nutrition: meal.nutrition
        }));
        
        // Add to container
        mealsContainer.appendChild(mealCard);
    });
    
    // Add event listeners for the new buttons
    document.querySelectorAll('.view-meal-details').forEach(button => {
        button.addEventListener('click', function() {
            const meal = JSON.parse(this.getAttribute('data-meal'));
            showMealDetails(meal);
        });
    });
    
    document.querySelectorAll('.save-meal').forEach(button => {
        button.addEventListener('click', function() {
            const meal = JSON.parse(this.getAttribute('data-meal'));
            saveMeal(meal);
        });
    });
}

// Save meal to history
function saveMeal(meal) {
    fetch('/api/save-meal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(meal)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Meal saved to history!', 'success');
        } else {
            showAlert(data.message || 'Failed to save meal', 'danger');
        }
    })
    .catch(error => {
        showAlert('An error occurred while saving meal', 'danger');
        console.error('Error:', error);
    });
}

// Setup Meal Detail Modal
function setupMealDetailModal() {
    // Setup event handlers for meal detail buttons in history page
    document.querySelectorAll('.view-meal-history-details').forEach(button => {
        button.addEventListener('click', function() {
            const mealId = this.getAttribute('data-meal-id');
            
            fetch(`/api/meal-details/${mealId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMealDetails(data.meal);
                    } else {
                        showAlert(data.message || 'Failed to load meal details', 'danger');
                    }
                })
                .catch(error => {
                    showAlert('An error occurred while loading meal details', 'danger');
                    console.error('Error:', error);
                });
        });
    });
}

// Show meal details in modal
function showMealDetails(meal) {
    const modal = document.getElementById('mealDetailModal');
    if (!modal) return;
    
    // Set meal data in modal
    modal.querySelector('.modal-title').textContent = meal.name;
    
    const descriptionEl = modal.querySelector('#mealDescription');
    if (descriptionEl) descriptionEl.textContent = meal.description;
    
    const ingredientsEl = modal.querySelector('#mealIngredients');
    if (ingredientsEl) {
        ingredientsEl.innerHTML = '';
        meal.ingredients.forEach(ingredient => {
            const li = document.createElement('li');
            li.textContent = ingredient;
            ingredientsEl.appendChild(li);
        });
    }
    
    const infoEl = modal.querySelector('#mealInfo');
    if (infoEl) {
        infoEl.innerHTML = `
            <p><strong>Meal Type:</strong> ${meal.meal_type || 'N/A'}</p>
            <p><strong>Price:</strong> KES ${meal.price}</p>
            <p><strong>Budget:</strong> KES ${meal.budget || 'N/A'}</p>
        `;
    }
    
    const nutritionEl = modal.querySelector('#nutritionInfo');
    if (nutritionEl && meal.nutrition) {
        nutritionEl.innerHTML = `
            <div class="d-flex justify-content-between mb-2">
                <span>Calories</span>
                <span>${meal.nutrition.calories} kcal</span>
            </div>
            <div class="d-flex justify-content-between mb-2">
                <span>Protein</span>
                <span>${meal.nutrition.protein}g</span>
            </div>
            <div class="d-flex justify-content-between mb-2">
                <span>Carbs</span>
                <span>${meal.nutrition.carbs}g</span>
            </div>
            <div class="d-flex justify-content-between mb-2">
                <span>Fat</span>
                <span>${meal.nutrition.fat}g</span>
            </div>
        `;
    }
    
    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alertsContainer');
    if (!alertsContainer) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsContainer.appendChild(alertDiv);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
} 