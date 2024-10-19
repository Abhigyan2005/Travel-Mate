document.addEventListener('DOMContentLoaded', function () {
    // Elements
    const planYourTripBtn = document.getElementById('planYourTripBtn');
    const tripModal = document.getElementById('tripModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const tripDetailsModal = document.getElementById('tripDetailsModal');
    const closeTripDetailsModal = document.getElementById('closeTripDetailsModal');
    const deleteForm = document.getElementById('deleteForm'); // Get the delete form
    
    let currentTripId = null; // Variable to store the selected trip ID

    // Open the "Plan Your Trip" modal
    planYourTripBtn.addEventListener('click', function () {
        tripModal.classList.remove('hidden');
    });

    // Close the "Plan Your Trip" modal
    closeModalBtn.addEventListener('click', function () {
        tripModal.classList.add('hidden');  // Hide the trip modal
    });

    // Close the trip details modal
    closeTripDetailsModal.addEventListener('click', function () {
        tripDetailsModal.classList.add('hidden');
        resetModal();  // Reset the modal contents when closed
    });

    // Show trip details in modal and update delete form
    function showTripDetails(tripId) {
        currentTripId = tripId;  // Store the current trip ID
        
        // Fetch the trip details from the backend or display modal with details
        fetch(`/trip-details/${tripId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch trip details: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                // Update modal content with trip details
                document.getElementById('modal-location').innerText = "Location: " + data.location;
                document.getElementById('modal-people').innerText = "Number of People: " + data.people;
                document.getElementById('modal-money').innerText = "Money Required: " + data.money_required;
                document.getElementById('modal-description').innerText = "Description: " + data.description;

                // Update the form action with the current trip ID
                deleteForm.setAttribute('action', `/delete-trip/${tripId}`);
                
                // Show the modal
                tripDetailsModal.classList.remove('hidden');
            })
            .catch(error => {
                console.error('Error fetching trip details:', error);  // Log any errors to the console
                alert('Failed to load trip details. Please try again later.');
            });
    }

    // Event listeners to show trip details when a trip is clicked
    document.querySelectorAll('.trip-card').forEach(card => {
        card.addEventListener('click', function () {
            const tripId = this.dataset.tripId;
            showTripDetails(tripId);
        });
    });

    // Delete trip action (optional: could trigger a confirmation modal before submitting)
    deleteForm.addEventListener('submit', function (event) {
        const confirmation = confirm("Are you sure you want to delete this trip?");
        if (!confirmation) {
            event.preventDefault();  // Prevent form submission if not confirmed
        }
    });

    // Reset the trip details modal contents
    function resetModal() {
        document.getElementById('modal-location').innerText = '';
        document.getElementById('modal-people').innerText = '';
        document.getElementById('modal-money').innerText = '';
        document.getElementById('modal-description').innerText = '';
        deleteForm.setAttribute('action', '#');  // Reset the delete form action
    }
});
